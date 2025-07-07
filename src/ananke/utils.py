#!/usr/bin/env python
"""
Module miscellaneous utilities
"""
from typing import Optional, Tuple, List, Union
from numpy.typing import NDArray
from functools import cached_property
import re
import docstring_parser as DS_parser
import numpy as np
from scipy import interpolate, spatial, optimize
from astropy import units, coordinates
import pandas as pd
import vaex
import cv2

from galaxia_ananke import utils as Gutils

__all__ = ['classproperty', 'compare_given_and_required', 'confirm_equal_length_arrays_in_dict', 'PDOrVaexDF', 'RecordingDataFrame', 'extract_parameters_from_docstring', 'extract_notes_from_docstring', 'LinearNDInterpolatorLOSExtrapolator']

classproperty = Gutils.classproperty

compare_given_and_required = Gutils.compare_given_and_required

confirm_equal_length_arrays_in_dict = Gutils.confirm_equal_length_arrays_in_dict

PDOrVaexDF = Union[pd.DataFrame, vaex.DataFrame]

class RecordingDataFrame(pd.DataFrame):
    """
    Pandas DataFrame that records all its used keys from getitem
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._record_of_all_used_keys = set()
    def _add_to_record_of_all_used_keys(self, keys):
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            self._record_of_all_used_keys.add(key)
    def __getitem__(self, key):
        self._add_to_record_of_all_used_keys(key)
        return super().__getitem__(key)
    # def __setitem__(self, key, value):
    #     self._add_to_record_of_all_used_keys(key)
    #     super().__setitem__(key, value)
    # def __delitem__(self, key):
    #     self._add_to_record_of_all_used_keys(key)
    #     super().__delitem__(key)
    @property
    def record_of_all_used_keys(self):
        return self._record_of_all_used_keys


def extract_parameters_from_docstring(docstring: str, parameters: Optional[List[str]] = None, ignore: Optional[List[str]] = None) -> str:
    input_DS = DS_parser.parse(docstring)
    output_DS = DS_parser.Docstring()
    output_DS.style = input_DS.style
    output_DS.meta = [param
                      for param in input_DS.params
                      if (True if parameters is None else param.arg_name in parameters) and (True if ignore is None else param.arg_name not in ignore)]
    temp_docstring = re.split("\n-*\n",DS_parser.compose(output_DS),maxsplit=1)[1]
    return '\n'.join([line if line[:1] in ['', ' '] else f"\n{line}" for line in temp_docstring.split('\n')])


def extract_notes_from_docstring(docstring: str) -> str:
    input_DS = DS_parser.parse(docstring)
    output_DS = DS_parser.Docstring()
    output_DS.style = input_DS.style
    output_DS.meta = [meta for meta in input_DS.meta if 'notes' in meta.args]
    return re.split("\n-*\n",DS_parser.compose(output_DS),maxsplit=1)[1]


class LinearNDInterpolatorNNExtrapolator:
    def __init__(self, points: NDArray, values: NDArray, **kwargs):
        """
        Use ND-linear interpolation over the convex hull of points, and nearest neighbor outside (for
        extrapolation)

        Idea taken from https://stackoverflow.com/questions/20516762/extrapolate-with-linearndinterpolator
        Adapted from https://stackoverflow.com/a/75327466
        """
        self.linear_interpolator = interpolate.LinearNDInterpolator(points, values, **kwargs)
        self.nearest_neighbor_interpolator = interpolate.NearestNDInterpolator(points, values, **kwargs)
        self._calibrating_center = np.mean(points,axis=0)
        self.linear_interpolator(self._calibrating_center)
        from_calibrating_center = points - self._calibrating_center
        self._calibrating_outer = self._calibrating_center + 2*from_calibrating_center[
            np.argmax(np.linalg.norm(from_calibrating_center)
                      if points.ndim == 2
                      else np.abs(from_calibrating_center))
                      ]
        self.nearest_neighbor_interpolator(self._calibrating_outer)

    def __call__(self, *args) -> Union[float, NDArray]:
        t = self.linear_interpolator(*args)
        t[np.isnan(t)] = self.nearest_neighbor_interpolator(*args)[np.isnan(t)]  # TODO reduce unnecessary interpolation use?
        if t.size == 1:
            return t.item(0)
        return t


class LinearNDInterpolatorLOSExtrapolator:
    def __init__(self, points: NDArray, values: NDArray, value_at_center: float = 0., spherical: bool = False, extrapolator: bool = True, **kwargs):
        """
        Use ND-linear interpolation over the convex hull of points, and line-of-sight last neighbor
        outside (for extrapolation)

        Idea adapted from
        - https://stackoverflow.com/questions/20516762/extrapolate-with-linearndinterpolator
        - https://stackoverflow.com/a/75327466
        - https://stackoverflow.com/a/30654855
        """
        self._spherical: bool = spherical
        self._extrapolator: bool = extrapolator
        points, values = self._complete_points_values_with_center(points, values, value_at_center, self._spherical)
        self.linear_interpolator = interpolate.LinearNDInterpolator(points, values, **kwargs)
        self._calibrating_center = np.mean(points,axis=0)
        self.linear_interpolator(self._calibrating_center)
        self._convex_hull = spatial.ConvexHull(self.linear_interpolator.tri.points[np.unique(self.linear_interpolator.tri.convex_hull)])
        self._mask_hull_faces = np.all((
            self._convex_hull.simplices
            if not self._spherical else
            self._convex_hull.points[:,0][self._convex_hull.simplices]
            ) != 0, axis=1)
        self._hull_vertices = self._convex_hull.points[self._convex_hull.simplices[self._mask_hull_faces]]
        # self._hull_circumcone_axes, self._hull_circumcone_angles = self._get_circumcone_axes_and_angles_of_simplices(self._convex_hull.points[self._convex_hull.simplices[self._mask_hull_faces]])
        # self._hull_circumcircle_centers, self._hull_circumcircle_radii = self._get_circumcircle_center_and_radii_of_simplices(self._convex_hull.points[self._convex_hull.simplices[self._mask_hull_faces],1:])
        self._hull_equations = self._convex_hull.equations[self._mask_hull_faces].T
        self._hull_normals, self._hull_offsets = self._hull_equations[:-1], self._hull_equations[-1]

    @cached_property
    def __hull_circumcone(self) -> Tuple[NDArray,NDArray]:
        return self._get_circumcone_axes_and_angles_of_simplices(self._hull_vertices)
    
    @property
    def _hull_circumcone_axes(self) -> NDArray:
        return self.__hull_circumcone[0]
    
    @property
    def _hull_circumcone_angles(self) -> NDArray:
        return self.__hull_circumcone[1]

    @cached_property
    def __hull_circumcircle(self) -> Tuple[NDArray,NDArray]:
        return self._get_circumcircle_center_and_radii_of_simplices(self._hull_vertices[...,1:])

    @property
    def _hull_circumcircle_centers(self) -> NDArray:
        return self.__hull_circumcircle[0]

    @property
    def _hull_circumcircle_radii(self) -> NDArray:
        return self.__hull_circumcircle[1]

    def __call__(self, *args) -> Union[float, NDArray]:
        xi = interpolate._interpolate._ndim_coords_from_arrays(args, ndim=self.linear_interpolator.points.shape[1])
        if self._spherical:  # if spherical, transform xi coordinates to [radius, lon, lat]
            xi = self._convert_cartesian_points_to_spherical(xi)
        # first run linear interpolator
        t = self.linear_interpolator(xi)
        if self._extrapolator:
            # assess if any value is nan and requires extrapolation
            t_is_nan = np.isnan(t)
            if t_is_nan.any():
                # convert args to xi
                xi_where_nan_t = xi[t_is_nan].T
                hull_mask = self._mask_hull_faces_likely_to_interest(xi_where_nan_t.T)
                if sum(hull_mask):
                    hull_vertices = self._hull_vertices[hull_mask]
                    hull_offsets = self._hull_offsets[hull_mask]
                    hull_normals = self._hull_normals.T[hull_mask]
                    # determine corresponding unitary LOS vectors
                    u_xi_where_nan_t = (xi_where_nan_t / np.linalg.norm(xi_where_nan_t, axis=0)
                                        if not self._spherical else
                                        np.array(xi_where_nan_t.shape[1]*[[1,0,0]]).T)
                    # compute alphas from LOS intersecting with all hull planes
                    if self._spherical:
                        shift = ([0,1,1]*xi_where_nan_t.T).T
                    offset = (hull_offsets
                            if not self._spherical else
                            hull_offsets+np.dot(hull_normals, shift).T)
                    alphas = -offset/np.dot(hull_normals, u_xi_where_nan_t).T
                    # force negative alphas to infinity...
                    alphas[alphas<=0] = np.inf
                    # ... to get the alphas we want as the minimum positive ones
                    intersecting_hull_face = np.argmin(alphas, axis=1)
                    alphas_on_hull = alphas[np.arange(alphas.shape[0]),intersecting_hull_face]
                    intersecting_hull_face_vertices = hull_vertices[intersecting_hull_face]
                    intersecting_hull_face_normals = hull_normals[intersecting_hull_face]
                    intersection = ((alphas_on_hull*u_xi_where_nan_t).T
                                    if not self._spherical else
                                    (alphas_on_hull*u_xi_where_nan_t+shift).T)
                    intersection_is_outside_face = np.any(  # if any difference of signs is not null, the point is outside the hull face
                        np.diff( # differentiate signs, to check if any difference is non-null
                            np.sign(np.sum(  # determine dot products between cross products and face normals, and return their sign
                                np.cross(  # compute cross products between vertice-to-intersection vectors and triangle side vectors 
                                    intersection[:,np.newaxis]-intersecting_hull_face_vertices,
                                    np.diff(intersecting_hull_face_vertices[:,[0,1,2,0]],axis=1),
                                    axis=2
                                )*intersecting_hull_face_normals[:,np.newaxis],
                                axis=2)).astype('int'),
                            axis=1)!=0,
                        axis=1)
                    # if not self._spherical:
                    #     intersection[intersection_is_outside_face] = 0.
                    # else:
                    #     intersection[intersection_is_outside_face, 0] = 0.
                    # compute run linear interpolator on corresponding positions
                    # TODO pre-allocate extrap_t?
                    extrap_t = self.linear_interpolator(intersection)
                    extrap_t[intersection_is_outside_face] = 0.  # TODO should be value_at_center: consider removing value_at_center and hardcoding 0. ?
                    # assess if any is still nan (due to machine precision)
                    extrap_t_is_nan = np.isnan(extrap_t)
                    while extrap_t_is_nan.any():
                        # replace the alphas by their previous values in machine precision (next towards 0)
                        alphas_on_hull[extrap_t_is_nan] = np.nextafter(alphas_on_hull[extrap_t_is_nan], 0)
                        # re-run linear interpolator
                        extrap_t[extrap_t_is_nan] = (
                            self.linear_interpolator((alphas_on_hull[extrap_t_is_nan]*u_xi_where_nan_t[:,extrap_t_is_nan]).T)
                            if not self._spherical else
                            self.linear_interpolator((alphas_on_hull[extrap_t_is_nan]*u_xi_where_nan_t[:,extrap_t_is_nan]+shift[:,extrap_t_is_nan]).T) 
                            )
                        # re-assess if still nan, and reloop if needed
                        extrap_t_is_nan = np.isnan(extrap_t)
                    # once loop is done, fill the nan that required extrapolation
                    t[t_is_nan] = extrap_t
                else:
                    t[t_is_nan] = 0.  # TODO should be value_at_center: consider removing value_at_center and hardcoding 0. ?
            # return the right format
            if t.size == 1:
                return t.item(0)
        return t
    
    def _mask_hull_faces_likely_to_interest(self, data_vectors: NDArray) -> NDArray:
        if not self._spherical:
            data_cone_axis, data_cone_angle = self._determine_smallest_cone_containing_points(data_vectors)
            return np.arccos(np.dot(self._hull_circumcone_axes, data_cone_axis)) < self._hull_circumcone_angles + data_cone_angle
        else:
            data_circle_center, data_circle_radius = self._determine_smallest_circle_enclosing_points(data_vectors[:,1:])
            return np.linalg.norm(self._hull_circumcircle_centers - data_circle_center, axis=1) < self._hull_circumcircle_radii + data_circle_radius

    @classmethod
    def _complete_points_values_with_center(cls, points: NDArray, values: NDArray,
                                                 value_at_center: float,
                                                 spherical: bool) -> Tuple[NDArray,NDArray]:
        if not spherical:
            center = points.shape[1]*[0.]
            if not center in points.tolist():
                points = np.vstack([center, points])
                values = np.hstack([value_at_center, values])
        else:
            # if spherical, transform points coordinates to [radius, lon, lat]
            points = cls._convert_cartesian_points_to_spherical(points)
            convex_hull = spatial.ConvexHull(points)
            # find hull faces that are almost parallel & nearest r=0 plane
            nearzero_faces = (np.abs(convex_hull.equations.T[0]) > np.linalg.norm(convex_hull.equations.T[[1,2]],axis=0)) & (convex_hull.equations.T[0] < 0)
            # find corresponding faces centroids
            nearzero_centroids = np.average(convex_hull.points[convex_hull.simplices[nearzero_faces]],axis=1)
            nearzero_centroids = nearzero_centroids[nearzero_centroids[:,0]!=0]
            # project them on r=0 plane
            nearzero_centroids[:,0] = 0.
            zero_convex_hull = spatial.ConvexHull(nearzero_centroids[:,1:])
            # mask border edges that are near parallel to actual -+180,-+90 box
            left_edges = (np.abs(zero_convex_hull.equations.T[0]) > np.abs(zero_convex_hull.equations.T[1])) & (zero_convex_hull.equations.T[0] < 0)
            right_edges = (np.abs(zero_convex_hull.equations.T[0]) > np.abs(zero_convex_hull.equations.T[1])) & (zero_convex_hull.equations.T[0] > 0)
            bottom_edges = (np.abs(zero_convex_hull.equations.T[0]) < np.abs(zero_convex_hull.equations.T[1])) & (zero_convex_hull.equations.T[1] < 0)
            top_edges = (np.abs(zero_convex_hull.equations.T[0]) < np.abs(zero_convex_hull.equations.T[1])) & (zero_convex_hull.equations.T[1] > 0)
            # find corresponding edge centroids
            left_edge_centroids = np.average(zero_convex_hull.points[zero_convex_hull.simplices[left_edges]],axis=1)
            right_edge_centroids = np.average(zero_convex_hull.points[zero_convex_hull.simplices[right_edges]],axis=1)
            bottom_edge_centroids = np.average(zero_convex_hull.points[zero_convex_hull.simplices[bottom_edges]],axis=1)
            top_edge_centroids = np.average(zero_convex_hull.points[zero_convex_hull.simplices[top_edges]],axis=1)
            # define ideal box (not necessarily -+180,-+90)
            box_limits = np.percentile(points[:,1:], [0,100], axis=0)
            # cut centroids already on box
            left_edge_centroids = left_edge_centroids[left_edge_centroids[:,0]!=box_limits[0,0]]
            right_edge_centroids = right_edge_centroids[right_edge_centroids[:,0]!=box_limits[1,0]]
            bottom_edge_centroids = bottom_edge_centroids[bottom_edge_centroids[:,1]!=box_limits[0,1]]
            top_edge_centroids = top_edge_centroids[top_edge_centroids[:,1]!=box_limits[1,1]]
            # project them onto corresponding box edge
            left_edge_centroids[:,0] = box_limits[0,0]
            right_edge_centroids[:,0] = box_limits[1,0]
            bottom_edge_centroids[:,1] = box_limits[0,1]
            top_edge_centroids[:,1] = box_limits[1,1]
            # make sure no latitude is duplicated on -+180 longitude edge
            if (box_limits[0,0] == -180)&(box_limits[1,0] == 180):
                left_edge_centroids = left_edge_centroids[~np.in1d(left_edge_centroids[:,1], right_edge_centroids[:,1])]
                right_edge_centroids = right_edge_centroids[~np.in1d(right_edge_centroids[:,1], left_edge_centroids[:,1])]
            # establish new corresponding border points
            border_centroids = np.vstack([left_edge_centroids, bottom_edge_centroids, top_edge_centroids, right_edge_centroids])
            border_centroids = np.hstack([np.zeros(border_centroids.shape[0])[:,np.newaxis], border_centroids])
            # establish complete set of points on r=0 plane, and append points and values accordingly
            zeros_centroids = np.vstack([nearzero_centroids, border_centroids])
            points = np.vstack([zeros_centroids, points])
            values = np.hstack([value_at_center*np.ones(zeros_centroids.shape[0]), values])
            # # extend & duplicate points beyond -+180 towards -+360 in longitude
            # points_left_mask = points[:,1] <= 0
            # points_right_mask = points[:,1] >= 0
            # points = np.vstack([points[points_right_mask]-[0,360,0], points, points[points_left_mask]+[0,360,0]])
            # values = np.hstack([values[points_right_mask], values, values[points_left_mask]])
            # add corner points if those are missing
            temp = points.tolist()
            corners = np.array([foo for l in box_limits[:,0] for b in box_limits[:,1] if not (foo:=[0.,l,b]) in temp])
            points = np.vstack([corners, points])
            values = np.hstack([value_at_center*np.ones(corners.shape[0]), values])
        return points, values

    @staticmethod
    def _convert_cartesian_points_to_spherical(points: NDArray) -> NDArray:
        r,lat,lon = coordinates.cartesian_to_spherical(*tuple(points.T))
        return np.array([
            r,
            (lon.to(units.deg)+180*units.deg)%(360*units.deg)-180*units.deg,
            lat.to(units.deg)
            ]).T
    
    @staticmethod
    def _get_circumcone_axes_and_angles_of_simplices(simplices: NDArray) -> Tuple[NDArray,NDArray]:
        # convert simplices vectors to unit vectors (uvec1, uvec2, uvec3)
        unit_temp = simplices / np.linalg.norm(simplices, axis=2)[..., np.newaxis]
        # determine potential cone axis as cross product of uvec2-uvec1 and uvec3-uvec2
        cone_axes = np.cross(*tuple(np.diff(unit_temp, axis=1).swapaxes(0,1)))
        # normalize and orient cone axes towards the hull faces
        cone_axes *= np.sign(cone_axes[:,np.newaxis] @ simplices[:,0][...,np.newaxis])[..., 0] / np.linalg.norm(cone_axes, axis=1)[..., np.newaxis]
        # find cone angle as the largest possible angle among all 3 angles between uveci and cone axes (should all be equal anyway)
        cone_angles = np.arccos(np.min((cone_axes[:,np.newaxis,np.newaxis] @ unit_temp[...,np.newaxis])[...,0,0], axis=1))
        return cone_axes, cone_angles

    @staticmethod    
    def _determine_smallest_cone_containing_points(points: NDArray) -> Tuple[NDArray,float]:
        # normalize points to unit sphere
        points /= np.linalg.norm(points, axis=1)[:, np.newaxis]
        # objective function: maximum angle for a given axis
        def objective(axis_vector):
            axis_vector = axis_vector / np.linalg.norm(axis_vector)
            return np.max(np.arccos(np.dot(points, axis_vector)))
        # initial guess: mean direction
        cone_axis_0 = np.mean(points, axis=0)
        cone_axis_0 /= np.linalg.norm(cone_axis_0)
        # optimize
        res = optimize.minimize(objective, cone_axis_0)
        cone_axis_opt = res.x / np.linalg.norm(res.x)
        cone_angle = objective(cone_axis_opt)
        return cone_axis_opt, cone_angle

    @staticmethod
    def _get_circumcircle_center_and_radii_of_simplices(triangles: NDArray) -> Tuple[NDArray,NDArray]:
        # https://en.wikipedia.org/wiki/Circumcircle#Circumcenter_vector
        # determine triangle opposite vertices lengths squared (a^2,b^2,c^2)
        triangle_sides_squared = np.sum(np.diff(triangles[:,[1,2,0,1]], axis=1)**2, axis=2)
        # derive from these the resulting barycentric coordinates of the circumcenter
        center_barycentric = triangle_sides_squared*np.sum([[[-1,1,1],[1,-1,1],[1,1,-1]]]*triangle_sides_squared[:,np.newaxis],axis=2)
        # and eventually the cartesian coordinates of the vector pointing to the circumcenter
        circumcenters = np.sum((center_barycentric/np.sum(center_barycentric, axis=1)[..., np.newaxis])[...,np.newaxis]*triangles, axis=1)
        # find the circumradii as the maximal possible one (all should be equal anyway)
        circumradii = np.max(np.linalg.norm(triangles - circumcenters[:,np.newaxis],axis=2), axis=1)
        return circumcenters, circumradii
    
    @staticmethod
    def _determine_smallest_circle_enclosing_points(points: NDArray) -> Tuple[NDArray,float]:
        center, radius = cv2.minEnclosingCircle(points.astype('float32'))
        return np.array(center), radius


if __name__ == '__main__':
    raise NotImplementedError()
