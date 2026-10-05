#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2022  Adrien CR Thob
#
# This file is part of the py-ananke project,
# <https://github.com/athob/py-ananke>, which is licensed
# under the GNU Affero General Public License v3.0 (AGPL-3.0).
# 
# The full copyright notice, including terms governing use, modification,
# and redistribution, is contained in the files LICENSE and COPYRIGHT,
# which can be found at the root of the source code distribution tree:
# - LICENSE <https://github.com/athob/py-ananke/blob/main/LICENSE>
# - COPYRIGHT <https://github.com/athob/py-ananke/blob/main/COPYRIGHT>
#
"""
Contains the KernelsDriver class definition

Please note that this module is private. The KernelsDriver class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Sequence, Dict, Callable
from numpy.typing import NDArray
from warnings import warn
import pathlib
import numpy as np
import enbid_ananke as EnBiD

from . import utils
from ._constants import *

if TYPE_CHECKING:
    from .Ananke import Ananke

__all__ = ['KernelsDriver']


class KernelsDriver:
    """
        Store the particle kernel characteristics and compute them if necessary.
    """
    _age_window_nodes_tag = "nodes"
    _age_window_kind_tag = "kind"
    _age_window_epsilon_tag = "epsilon"
    _age_window_width_tag = "width"
    _default_age_window = {
        _age_window_nodes_tag:   1,
        _age_window_kind_tag:    "piecewise_constant",
        _age_window_epsilon_tag: 0.0,
        _age_window_width_tag:   1.0,
    }
    _valid_age_window_kinds = ("hat", "gaussian", "piecewise_constant")
    _kernels = 'kernels'
    def __init__(self, ananke: Ananke, kernels_estimator: Optional[Callable] = None,
                 structures: Optional[Dict[str, Dict[str, Any]]] = None, field: Optional[Dict[str, Any]] = None,
                 **kwargs: Dict[str, Any],
    ) -> None:
        """
            Parameters
            ----------
            ananke : Ananke object
                The Ananke object that utilizes this KernelsDriver object.

            kernels_estimator : callable
                TODO

            structures : dict or None, optional
                Mapping from a structure name to its configuration. Each value
                is a dict with the following keys:

                'mask' : array_like of bool, shape (N,)
                    Boolean array selecting the particles belonging to this
                    structure. Masks of different structures must be disjoint;
                    an overlap raises a ValueError at kernel-computation time.

                'age_window' : dict or None, optional
                    Age-window configuration applied to this structure's
                    particles. If None, the structure is processed in a single
                    estimator run (no age conditioning). If a dict, the
                    following keys are recognised; any missing key takes its
                    default:

                    'nodes' : int or 1-D sequence of float, default 1
                        Either the number of age nodes to place at quantiles
                        of the structure's age distribution, or an explicit
                        sequence of node locations in log-age. The number of
                        distinct nodes equals the number of estimator runs on
                        this structure.

                    'kind' : str or callable, default 'piecewise_constant'
                        Window shape for the age partition of unity. One of
                        'piecewise_constant' (reproduces hard binning, each
                        particle covered by exactly 1 window), 'hat' (linear
                        B-spline, each particle covered by at most 2 windows),
                        or 'gaussian' (normalized-Gaussian partition, each
                        particle covered by all windows). Alternatively, a
                        callable ``profile(t)`` mapping a dimensionless
                        coordinate t (0 at a node, ±1 at the adjacent node
                        under ``width=1``) to an unnormalized weight; rows are
                        normalized by the driver.

                    'epsilon' : float, default 0.0
                        Weight threshold below which a window is dropped
                        without an estimator call. Ignored by
                        'piecewise_constant'.

                    'width' : float, default 1.0
                        Window width as a multiple of the local node spacing.
                        For 'piecewise_constant', the bin edge sits at
                        ``width/2`` spacings from the node; for 'hat', the
                        support reaches ``width`` spacings; for 'gaussian',
                        sigma equals ``width`` spacings.

                If None, no structures are defined and every particle is
                handled by ``catchall``.

            field : dict or None, optional
                Age-window configuration applied to field particles — those
                not assigned to any structure mask, i.e. the smooth,
                unstructured component. Accepts the same keys as a
                structure's 'age_window' entry (see above). If None, the
                default config is used, which is a single estimator run with
                no age conditioning. When ``structures`` is None, the field
                covers every particle, so ``KernelsDriver(..., field=<cfg>)``
                applies ``<cfg>`` to the whole population.

            **kwargs
                Additional parameters to be used by the kernels estimator. In
                the current implementation, these include all the configurable
                parameters of EnBiD accessible through the class method
                display_EnBiD_docs (except `name` and `ngb`).
        """
        self.__ananke: Ananke = ananke
        self.__kernels_estimator: Optional[Callable] = kernels_estimator
        self.__structures = self._parse_structures(structures)
        self.__field = self._parse_age_window(field)
        self.__parameters: Dict[str, Any] = kwargs
        self.kernels = self.particle_kernels

    @classmethod
    def _parse_structures(cls, structures):
        """
        Validate and normalize the ``structures`` dict.

        Each value must be a dict with a required 'mask' (bool array of
        shape (N,), validated on access) and an optional 'age_window'
        (passed to ``_parse_age_window``; None yields the default
        single-run config).
        """
        if structures is None:
            return {}
        if not isinstance(structures, dict):
            raise TypeError(
                f"structures must be a dict or None, got "
                f"{type(structures).__name__}"
            )
        out = {}
        for name, spec in structures.items():
            if not isinstance(spec, dict):
                raise TypeError(
                    f"structures[{name!r}] must be a dict, got "
                    f"{type(spec).__name__}"
                )
            if "mask" not in spec:
                raise KeyError(
                    f"structures[{name!r}] is missing required key 'mask'"
                )
            out[name] = {
                "mask":       np.asarray(spec["mask"], dtype=bool),
                "age_window": cls._parse_age_window(spec.get("age_window")),
            }
        return out

    @classmethod
    def _parse_age_window(cls, age_window):
        """
        Validate and normalize an ``age_window`` configuration. Missing
        keys take values from ``_default_age_window``; passing None yields
        the default config, which is a single piecewise-constant window —
        i.e. a single estimator run with no age conditioning.
        """
        if age_window is None:
            age_window = {}
        if not isinstance(age_window, dict):
            raise TypeError(
                f"age_window must be a dict or None, got "
                f"{type(age_window).__name__}"
            )
        unknown = set(age_window) - set(cls._default_age_window)
        if unknown:
            raise KeyError(
                f"age_window has unknown key(s): {sorted(unknown)}; "
                f"valid keys are {sorted(cls._default_age_window)}"
            )
        cfg = {**cls._default_age_window, **age_window}
        kind = cfg[cls._age_window_kind_tag]
        if not callable(kind) and kind not in cls._valid_age_window_kinds:
            raise ValueError(
                f"age_window['{cls._age_window_kind_tag}'] = {kind!r}; expected one of "
                f"{cls._valid_age_window_kinds}, or a callable "
                f"profile(t)."
            )
        cfg[cls._age_window_epsilon_tag] = float(cfg[cls._age_window_epsilon_tag])
        if cfg[cls._age_window_epsilon_tag] < 0.0:
            raise ValueError(f"age_window['{cls._age_window_epsilon_tag}'] must be >= 0")
        cfg[cls._age_window_width_tag] = float(cfg[cls._age_window_width_tag])
        if cfg[cls._age_window_width_tag] <= 0.0:
            raise ValueError(f"age_window['{cls._age_window_width_tag}'] must be > 0")
        return cfg

    @classmethod
    def _check_kernels_format(self, kernels):
        if kernels is not None:
            pass  # TODO
            # if isinstance(kernels, NDArray):
            #     utils.compare_given_and_required(kernels.keys(), optional={POS_TAG, VEL_TAG}, error_message="Given kernels dictionary has wrong set of keys")
            #     utils.confirm_equal_length_arrays_in_dict(kernels, error_message_dict_name="kernels")
            # else:
            #     raise ValueError("Kernels should be either None or an array-like")

    def _compute_kernels(self):
        """
        Generate via the estimator given at class construction the array
        of kernel-size estimates needed to generate the survey.

        Each entry in ``self.structures`` is processed independently with
        its own age-window config. Particles not covered by any structure
        are processed with ``self.catchall_age_window``. Masks must be
        disjoint.

        Returns
        ----------
        kernels : array_like
            A (Nx2) array of kernel-size estimates for the pipeline
            particles.
        """
        N = self.particle_positions.shape[0]
        kernels = np.full((N, 2), np.nan, dtype=float)
        covered = np.zeros(N, dtype=bool)

        for name, struct in self.structures.items():
            mask = struct["mask"]
            if mask.shape != (N,):
                raise ValueError(
                    f"structures[{name!r}]['mask'] has shape {mask.shape}, "
                    f"expected ({N},)"
                )
            if np.any(covered & mask):
                raise ValueError(
                    f"structures[{name!r}]['mask'] overlaps with an "
                    f"earlier structure's mask; masks must be disjoint."
                )
            if mask.any():
                kernels[mask] = self.__compute_group_kernels(
                    mask, struct["age_window"]
                )
            covered |= mask

        remainder = ~covered
        if remainder.any():
            kernels[remainder] = self.__compute_group_kernels(
                remainder, self.field
            )

        if np.isnan(kernels).any():
            raise RuntimeError(
                "Some particles received no kernel estimate; this "
                "indicates a coverage bug."
            )

        self.kernels = kernels
        return self.kernels

    def __compute_group_kernels(self, mask, age_window_config):
        """
        Compute kernels for the subset selected by ``mask`` using the
        given (already parsed) age-window config. If the config resolves
        to a single window (nodes=1), this reduces to one estimator call.
        """
        ages = self.particle_ages
        if ages is None:
            # No ages available: single estimator run regardless of config.
            return self.__call_kernel_estimator(mask)

        idx = np.flatnonzero(mask)
        ages_in = np.asarray(ages)[idx]

        nodes = self.__place_age_nodes(ages_in, age_window_config)
        K = nodes.size

        W = self.__age_partition_of_unity(ages_in, nodes, age_window_config)

        kernel_acc = np.zeros((idx.size, 2), dtype=float)
        weight_acc = np.zeros(idx.size, dtype=float)

        epsilon = age_window_config[self._age_window_epsilon_tag]

        for k in range(K):
            w_k = W[:, k]
            active = w_k > epsilon
            if not active.any():
                continue

            sub_mask = np.zeros_like(mask)
            sub_mask[idx[active]] = True

            h_k = self.__call_kernel_estimator(
                sub_mask, mass_weights=w_k[active]
            )
            kernel_acc[active] += w_k[active, None] * h_k
            weight_acc[active] += w_k[active]

        weight_acc = np.where(weight_acc > 0.0, weight_acc, 1.0)
        return kernel_acc / weight_acc[:, None]

    def __call_kernel_estimator(self, mask, mass_weights=None):
        """
        Run the black-box estimator on the subset selected by ``mask``.
        If ``mass_weights`` is given (shape == mask.sum()), the masses
        passed to the estimator are multiplied elementwise — this is
        how the soft-window weighting is injected.
        """
        pos = self.particle_positions[mask]
        vel = self.particle_velocities[mask]
        m = self.particle_masses[mask]
        if mass_weights is not None:
            m = m * mass_weights
        return self._kernels_estimator(
            pos, vel, m,
            ngb=self.ngb,
            **self.parameters,
        )

    @classmethod
    def __place_age_nodes(cls, ages_in, config):
        """
        Resolve the ``nodes`` entry of an age-window config into a
        sorted, duplicate-free array of node locations.

        Two accepted forms
        ------------------
        int
            Number of nodes K. Placed at quantiles of ``ages_in``
            (K=1 -> median).
        array_like of float
            Explicit node locations. Used as-is after sorting and
            removing duplicates; the resulting count is the number of
            estimator runs for this group.

        Parameters
        ----------
        ages_in : array_like, shape (M,)
            Ages of the particles in the group being processed.
        config : dict
            A normalized age-window configuration, as produced by
            ``_parse_age_window``.

        Returns
        -------
        nodes : ndarray, shape (K,)
            Sorted, duplicate-free node locations.
        """
        spec = config[cls._age_window_nodes_tag]
        if isinstance(spec, (int, np.integer)):
            K = int(spec)
            if K < 1:
                raise ValueError(f"age_window['{cls._age_window_nodes_tag}'] must be >= 1")
            if K == 1:
                nodes = np.array([np.median(ages_in)], dtype=float)
            else:
                qs = np.linspace(0.0, 1.0, K)
                nodes = np.quantile(ages_in, qs)
            # Quantiles can collide at the tails (e.g. many identical
            # ages); unique() collapses duplicates so the downstream
            # partition stays well-defined.
            return np.unique(nodes)
        if isinstance(spec, (float, np.floating)):
            raise TypeError(
                f"age_window['{cls._age_window_nodes_tag}'] got a float; pass an int (node count) "
                "or an explicit sequence of node locations."
            )
        nodes = np.asarray(spec, dtype=float)
        if nodes.ndim != 1:
            raise ValueError(
                f"age_window['{cls._age_window_nodes_tag}'] array must be 1-D, got shape {nodes.shape}"
            )
        if nodes.size == 0:
            raise ValueError(f"age_window['{cls._age_window_nodes_tag}'] array is empty")
        if not np.all(np.isfinite(nodes)):
            raise ValueError(f"age_window['{cls._age_window_nodes_tag}'] contains non-finite values")
        return np.unique(nodes)

    @classmethod
    def __age_partition_of_unity(cls, ages_in, nodes, config):
        """
        Compute a partition of unity over ``nodes`` for the given ages.

        Every kind shares the same structure: for each node c with
        neighboring nodes on either side, an age x is mapped to a
        dimensionless coordinate ``t = (x - c) / (width * scale)``,
        where ``scale`` is the distance to the neighboring node on the
        same side of c, and the weight is ``profile(t)`` for a
        kind-specific profile. Rows are then normalized to sum to 1.
        Ages whose profile support does not cover them (compact kinds
        with ages outside the node range, or between supports when
        width < 1) are assigned wholly to the nearest node.

        Parameters
        ----------
        ages_in : array_like, shape (M,)
            Ages at which to evaluate the basis. Need not be sorted.
        nodes : array_like, shape (K,)
            Sorted, duplicate-free node locations, as produced by
            ``__place_age_nodes``.
        config : dict
            A normalized age-window configuration.

        Returns
        -------
        W : ndarray, shape (M, K)
            Weight matrix whose rows sum to 1.
        """
        ages_in = np.asarray(ages_in)
        nodes = np.asarray(nodes)
        M = ages_in.size
        K = nodes.size

        if K == 1:
            return np.ones((M, 1), dtype=float)

        # Local asymmetric scale: distance to the previous node
        # (scale_left) and to the next node (scale_right). Boundary
        # nodes reuse the one spacing they have on both sides.
        d = np.diff(nodes)
        scale_left  = np.concatenate(([d[0]],  d))
        scale_right = np.concatenate(( d, [d[-1]]))

        scale_mult, profile = cls.__age_window_profile(
            config[cls._age_window_kind_tag],
            config[cls._age_window_width_tag],
        )

        # Signed distance to each node, and the corresponding local
        # scale on that side. searchsorted is not needed here: the
        # piecewise behavior comes entirely from `scale` and `profile`.
        diff  = ages_in[:, None] - nodes[None, :]
        scale = np.where(diff < 0.0,
                        scale_left[None, :],
                        scale_right[None, :])
        t = diff / (scale_mult * scale)
        W: NDArray = profile(t)

        # Normalize rows to sum to 1.
        row_sum = W.sum(axis=1, keepdims=True)
        nonzero = row_sum[:, 0] > 0.0
        W[nonzero] /= row_sum[nonzero]

        # Rows with no contribution (compact profiles with ages outside
        # the covered range): assign wholly to the nearest node.
        empty = ~nonzero
        if empty.any():
            idx = np.flatnonzero(empty)
            nearest = np.argmin(
                np.abs(ages_in[idx, None] - nodes[None, :]), axis=1
            )
            W[idx] = 0.0
            W[idx, nearest] = 1.0

        return W

    @classmethod
    def __age_window_profile(cls, kind, width):
        """
        Return ``(scale_multiplier, profile)`` for the requested
        age-window kind.

        ``profile(t)`` maps a dimensionless coordinate (0 at a node,
        ±1 at the adjacent node under ``width=1``) to a weight,
        elementwise. ``scale_multiplier`` rescales the local node
        spacing before forming ``t``, so a single profile shape can be
        reused at different effective widths.

        ``kind`` may be one of the named profiles below, or a
        user-supplied callable ``profile(t)`` taking the same
        dimensionless argument (see the ``structures`` docstring).
        To add a new named kind, add an entry here; the driver does
        not need to change.
        """
        if callable(kind):
            return width, kind
        if kind == "piecewise_constant":
            return width, lambda t: (np.abs(t) < 0.5).astype(float)
        if kind == "hat":
            return width, lambda t: np.maximum(0.0, 1.0 - np.abs(t))
        if kind == "gaussian":
            return width, lambda t: 2**(-4 * t * t)  # = np.exp(-4*np.ln(2) * t * t)
        raise ValueError(
            f"Unknown age_window['{cls._age_window_kind_tag}'] = {kind!r}; expected one of "
            f"'piecewise_constant', 'hat', 'gaussian', or a callable."  # TODO modularize?
        )

    def _run_enbid(self):
        warn('This method will be deprecated, please use instead method _compute_kernels', DeprecationWarning, stacklevel=2)
        return self._compute_kernels()

    def __enbid_kernel_estimator(self, positions, velocities, masses, **kwargs):
        path = pathlib.Path(self.name)
        rho_pos = EnBiD.enbid(positions, mass=masses, name=path / POS_TAG, **kwargs)
        rho_vel = EnBiD.enbid(velocities, mass=masses, name=path / VEL_TAG, **kwargs)
        rho = EnBiD.enbid(positions, velocities=velocities, mass=masses, name=path / (POS_TAG+VEL_TAG), **kwargs)
        kernels_from_3d = np.cbrt(masses/(np.vstack([rho_pos, rho_vel])*4/3*np.pi)).T
        normalization_factors = ((masses/rho)/(np.pi**3/6*np.prod(kernels_from_3d**3, axis=1)))[:,None]**(1/6)
        kernels = normalization_factors*kernels_from_3d
        return kernels

    @property
    def _kernels_estimator(self) -> Callable:
        if self.__kernels_estimator is None:
            return self.__enbid_kernel_estimator
        else:
            return self.__kernels_estimator

    @property
    def structures(self):
        """The normalized structures dict (read-only view)."""
        return self.__structures

    @property
    def field(self):
        """The normalized age-window config applied to uncovered particles."""
        return self.__field

    @property
    def ananke(self):
        return self.__ananke
    
    @property
    def particle_positions(self):
        return self.ananke.particle_positions
    
    @property
    def particle_velocities(self):
        return self.ananke.particle_velocities

    @property
    def particle_masses(self):
        return self.ananke.particle_masses

    @property
    def particle_ages(self):
        return self.ananke.particle_ages

    @property
    def particle_kernels(self) -> Optional[NDArray]:
        if self._kernels in self.ananke.particles:
            return self.ananke.particles[self._kernels]
        elif 'rho_pos' in self.ananke.particles:
            warn("The use of 'rho_pos' and 'rho_vel' keys to provide density estimates that inform kernels sizes will be removed in a future update in favour of the currently supported key 'kernels' to directly provides those kernel sizes", DeprecationWarning, stacklevel=2)
            particle_densities_stack = [self.ananke.particles['rho_pos']]
            if 'rho_vel' in self.ananke.particles:
                particle_densities_stack.append(self.ananke.particles['rho_vel'])
            return 1/np.cbrt(4/3*np.pi*np.vstack(particle_densities_stack).T)
    
    @property
    def name(self):
        return self.ananke.name

    @property
    def ngb(self):
        return self.ananke.ngb

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters
    
    @property
    def kernels(self):
        if self.__kernels is not None:
            return self.__kernels
        else:
            return self._compute_kernels()
    
    @kernels.setter
    def kernels(self, kernels):
        self._check_kernels_format(kernels)
        self.__kernels = kernels
    
    @classmethod
    def display_EnBiD_docs(cls):
        """
            Print the EnBiD.run_enbid docstring
        """
        print(EnBiD.run_enbid.__doc__)


if __name__ == '__main__':
    raise NotImplementedError()
