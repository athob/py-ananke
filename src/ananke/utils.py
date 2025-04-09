#!/usr/bin/env python
"""
Module miscellaneous utilities
"""
from typing import Optional, List, Union
from numpy.typing import NDArray
import re
import docstring_parser as DS_parser
import numpy as np
from scipy import interpolate, spatial
from astropy import units, coordinates
import pandas as pd
import vaex

from Galaxia_ananke import utils as Gutils

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
    def __init__(self, points: NDArray, values: NDArray, value_at_center: float = 0., spherical: bool = True, **kwargs):
        """
        Use ND-linear interpolation over the convex hull of points, and line-of-sight last neighbor
        outside (for extrapolation)

        Idea adapted from
        - https://stackoverflow.com/questions/20516762/extrapolate-with-linearndinterpolator
        - https://stackoverflow.com/a/75327466
        - https://stackoverflow.com/a/30654855
        """
        self._spherical: bool = spherical
        if not self._spherical:
            center = points.shape[1]*[0.]
            if not center in points.tolist():
                points = np.vstack([center, points])
                values = np.hstack([value_at_center, values])
        else:
            # if spherical, transform points coordinates to [radius, lon, lat]
            points = self._convert_cartesian_points_to_spherical(points)
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
            left_edge_centroids = left_edge_centroids[left_edge_centroids[:,0]!=-180]
            right_edge_centroids = right_edge_centroids[right_edge_centroids[:,0]!=180]
            bottom_edge_centroids = bottom_edge_centroids[bottom_edge_centroids[:,1]!=-90]
            top_edge_centroids = top_edge_centroids[top_edge_centroids[:,1]!=90]
            # project them onto corresponding box edge
            left_edge_centroids[:,0] = -180
            right_edge_centroids[:,0] = 180
            bottom_edge_centroids[:,1] = -90
            top_edge_centroids[:,1] = 90
            # make sure no latitude is duplicated on -+180 longitude edge
            left_edge_centroids = left_edge_centroids[~np.in1d(left_edge_centroids[:,1], right_edge_centroids[:,1])]
            right_edge_centroids = right_edge_centroids[~np.in1d(right_edge_centroids[:,1], left_edge_centroids[:,1])]
            # establish new corresponding border points
            border_centroids = np.vstack([left_edge_centroids, bottom_edge_centroids, top_edge_centroids, right_edge_centroids])
            border_centroids = np.hstack([np.zeros(border_centroids.shape[0])[:,np.newaxis], border_centroids])
            # establish complete set of points on r=0 plane, and append points and values accordingly
            zeros_centroids = np.vstack([nearzero_centroids, border_centroids])
            points = np.vstack([zeros_centroids, points])
            values = np.hstack([value_at_center*np.ones(zeros_centroids.shape[0]), values])
            # extend & duplicate points beyond -+180 towards -+360 in longitude
            points_left_mask = points[:,1] <= 0
            points_right_mask = points[:,1] >= 0
            points = np.vstack([points[points_right_mask]-[0,360,0], points, points[points_left_mask]+[0,360,0]])
            values = np.hstack([values[points_right_mask], values, values[points_left_mask]])
            # add corner points if those are missing
            temp = points.tolist()
            corners = np.array([foo for l in [-180.,180.] for b in [-90.,90.] if not (foo:=[0.,l,b]) in temp])
            points = np.vstack([corners, points])
            values = np.hstack([value_at_center*np.ones(corners.shape[0]), values])
        #
        self.linear_interpolator = interpolate.LinearNDInterpolator(points, values, **kwargs)
        self._calibrating_center = np.mean(points,axis=0)
        self.linear_interpolator(self._calibrating_center)
        # from_calibrating_center = points - self._calibrating_center
        # self._calibrating_outer = self._calibrating_center + 2*from_calibrating_center[
        #     np.argmax(np.linalg.norm(from_calibrating_center)
        #               if points.ndim == 2
        #               else np.abs(from_calibrating_center))
        #               ]
        self._convex_hull = spatial.ConvexHull(self.linear_interpolator.tri.points[np.unique(self.linear_interpolator.tri.convex_hull)])
        self._hull_equations = self._convex_hull.equations.T
        self._hull_normals, self._hull_offsets = self._hull_equations[:-1], self._hull_equations[-1]

    def __call__(self, *args) -> Union[float, NDArray]:
        xi = interpolate._interpolate._ndim_coords_from_arrays(args, ndim=self.linear_interpolator.points.shape[1])
        if self._spherical:  # if spherical, transform xi coordinates to [radius, lon, lat]
            xi = self._convert_cartesian_points_to_spherical(xi)
        # first run linear interpolator
        t = self.linear_interpolator(xi)
        # assess if any value is nan and requires extrapolation
        t_is_nan = np.isnan(t)
        if t_is_nan.any():
            # convert args to xi
            xi_where_nan_t = xi[t_is_nan].T
            # determine corresponding unitary LOS vectors
            u_xi_where_nan_t = (xi_where_nan_t / np.linalg.norm(xi_where_nan_t, axis=0)
                                if not self._spherical else
                                np.array(xi_where_nan_t.shape[1]*[[1,0,0]]).T)
            # compute alphas from LOS intersecting with all hull planes
            if self._spherical:
                shift = ([0,1,1]*xi_where_nan_t.T).T
            offset = (self._hull_offsets
                      if not self._spherical else
                      self._hull_offsets+np.dot(self._hull_normals.T, shift).T)
            alphas = -offset/np.dot(self._hull_normals.T, u_xi_where_nan_t).T
            # force negative alphas to infinity...
            alphas[alphas<=0] = np.inf
            # ... to get the alphas we want as the minimum positive ones
            alphas_on_hull = np.min(alphas, axis=1)
            # compute run linear interpolator on corresponding positions
            extrap_t = (self.linear_interpolator((alphas_on_hull*u_xi_where_nan_t).T)
                        if not self._spherical else
                        self.linear_interpolator((alphas_on_hull*u_xi_where_nan_t+shift).T))
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
        # return the right format
        if t.size == 1:
            return t.item(0)
        return t
    
    @staticmethod
    def _convert_cartesian_points_to_spherical(points: NDArray) -> NDArray:
        r,lat,lon = coordinates.cartesian_to_spherical(*tuple(points.T))
        return np.array([
            r,
            (lon.to(units.deg)+180*units.deg)%(360*units.deg)-180*units.deg,
            lat.to(units.deg)
            ]).T


if __name__ == '__main__':
    raise NotImplementedError()
