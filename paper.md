---
title: Generating synthetic star catalogs from simulated data for next-gen observatories with ``py-ananke``
tags:
  - Python
  - C++
  - astronomy
  - galaxies
  - stars
  - simulations
  - mock observations
authors:
  - name: Adrien C.R. Thob
    orcid: 0000-0001-7928-1973
    corresponding: true
    affiliation: 1
  - name: Robyn E. Sanderson
    orcid: 0000-0003-3939-3297
    affiliation: 1
  - name: Andrew P. Eden
    orcid: 0009-0004-2146-4856
    affiliation: 2
  - name: Farnik Nikakhtar
    orcid: 0000-0002-3641-4366
    affiliation: 3
  - name: Nondh Panithanpaisal
    orcid: 0000-0001-5214-8822
    affiliation: "1,4,5"
  - name: Nicolás Garavito-Camargo
    orcid: 0000-0001-7107-1744
    affiliation: 6
  - name: Sanjib Sharma
    orcid: 0000-0002-0920-809X
    affiliation: 7
affiliations:
 - name: Department of Physics & Astronomy, University of Pennsylvania, 209 S 33rd Street, Philadelphia, PA 19104, USA 
   index: 1
 - name: Department of Aerospace, Physics and Space Sciences, Florida Institute of Technology, Melbourne, FL 32901, USA
   index: 2
 - name: Department of Physics, Yale University, New Haven, CT 06511, USA
   index: 3
 - name: The Observatories of the Carnegie Institution for Science, 813 Santa Barbara Street, Pasadena, CA 91101, USA
   index: 4
 - name: TAPIR, Mailcode 350-17, California Institute of Technology, Pasadena, CA 91125, USA
   index: 5
 - name: Center for Computational Astrophysics, Flatiron Institute, Simons Foundation, 162 Fifth Avenue, New York, NY 10010, USA
   index: 6
 - name: Space Telescope Science Institute, 3700 San Martin Drive, Baltimore, MD 21218, USA
   index: 7
date: 1 October 2023
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
# aas-doi: ?
# aas-journal: ?
---

# Summary

We find ourselves on the brink of an exciting era in observational astrophysics, driven by groundbreaking facilities like JWST, Euclid, Rubin, Roman, SKA, or ELT. Simultaneously, computational astrophysics has shown significant strides, yielding highly realistic galaxy formation simulations, thanks to both hardware and software enhancements. Bridging the gap between simulations and observations has become paramount for meaningful comparisons.

We introduce ``py-ananke``, a ``Python`` pipeline designed to generate synthetic resolved stellar surveys from cosmological simulations, adaptable to various instruments. Building upon its predecessor, ``ananke`` by @Sanderson:2020, which produced Gaia DR2 mock star surveys, the ``py-ananke`` package offers a user-friendly "plug & play" experience. The pipeline employs cutting-edge phase-space density estimation and initial mass function sampling to convert particle data into synthetic stars, while interpolating pre-computed stellar isochrone tracks for photometry. Additionally, it includes modules for estimating interstellar reddening, dust-induced extinctions, and for quantifying errors through dedicated modeling approaches. ``py-ananke`` promises to serve as a vital bridge between computational astrophysics and observational astronomy, facilitating preparations and making scientific predictions for the next generation of telescopes.


# Statement of need

The upcoming decade holds promise for groundbreaking discoveries, thanks to a multitude of recent and forthcoming observational facilities. The James Webb Space Telescope [@JWST:2006], for instance, with its exceptional specifications, has already delved into early universe galaxies with unprecedented detail, revealing their rich diversity [@Ferreira:2022;@Adams:2023;@Finkelstein:2023;@Kocevski:2023;@Kartaltepe:2023;@PerezGonzalez:2023;@Harikane:2023;@Hsiao:2023;@Trussler:2023;@Casey:2023;@Ferreira:2023;@Eisenstein:2023]. The recently launched Euclid Telescope [@Euclid:2011] promises to shed light on the universe's accelerating expansion by surveying an immense number of galaxies [@EuclidCollaboration:2022]. The Vera Rubin Observatory [@Rubin:2019], with first light expected soon, will precisely map the Milky Way (MW) up to the virial radius and nearby galaxies, providing exceptional stellar astrometry data. Furthermore, the Nancy Grace Roman Space Telescope [@Roman:2019], set to launch in the next couple of years, will offer a wide field of view for deep-sky near-infrared exploration, facilitating the study of resolved stellar populations in nearby galaxies [@Dey:2023;@Han:2023]. However, these observatories will generate an unprecedented amount of raw data, necessitating community preparedness.

In parallel, a number of projects have emerged over the last decade in computational astrophysics, continuously surpassing hardware and software limits to simulate galaxy formation in a cosmological context realistically [@Stinson:2010;@Stinson:2013;@Hirschmann:2014;@Dubois:2014;@Vogelsberger:2014;@Hopkins:2014;@Schaye:2015;@Crain:2015;@Khandai:2015;@Wang:2015;@Dolag:2015;@Dolag:2016;@Feng:2016;@Dave:2016;@Tremmel:2017;@Nelson:2018;@Pillepich:2018;@Springel:2018;@Henden:2018;@Hopkins:2018;@Pfeffer:2018;@Kruijssen:2019;@Peeples:2019;@Dave:2019;@Bastian:2020;@Agertz:2021;@Dubois:2021;@Applebaum:2021;@Hopkins:2023;@Rey:2023;@Feldmann:2023;@Schaye:2023;@Pakmor:2023]. These simulations serve as invaluable test beds for tools developed in anticipation of the next-generation telescope era, but also for our own models. However, translating these simulations into mock observables is challenging due to the representation of stellar populations as star particles, with each particle representing a total stellar mass between $10^3$ and $10^8$ times the mass of the Sun. To compare simulations with real data, one must break down these particles into individual stars consistently. Since the simulation resolution is not "one star particle per star" in the vast majority of these simulations, producing mock observables necessarily requires a series of assumptions that can have different effects on the final prediction. 

This challenge was addressed by @Sanderson:2020 when producing a mock Gaia DR2 catalog from Milky-Way-mass simulated galaxies in the latte suite of FIRE simulations [@Wetzel:2016] using the so-called ``ananke`` pipeline. They used phase-space density estimation and initial mass function sampling to transform particle data into individual synthetic stars, retaining parent particle age and metallicity. Photometry was determined by interpolating pre-computed stellar isochrone tracks from the Padova database [@Marigo:2017] based on star mass, age, and metallicity. Additional post-processing included estimating interstellar reddening, per-band dust extinctions using metal-enriched gas distribution, and error quantification based on a model described by functions calibrated to [@Gaia:2018] characterizations. Each different step of the process, and its associated assumptions, was modularized and its assumptions documented, both to understand and isolate the effect of each assumption on the final product and to retain enough information at each step that a change to one assumption did not necessarily require re-producing the predictions from scratch.

The ``ananke`` pipeline by @Sanderson:2020, though powerful, lacks user-friendliness and flexibility. It is challenging to integrate into other pipelines and expand beyond the Gaia photometric system. The development of ``py-ananke`` aims to make this framework more accessible to a wider community. By providing a self-contained and easily installable ``Python`` package, it streamlines the ``ananke`` pipeline, automating tasks previously requiring manual intervention. ``py-ananke`` also expands ``ananke``'s photometric system support and employs a modular implementation for future enhancements. It promises a smoother upgrade path for users.

# Infrastructure

The implementation of ``py-ananke`` is designed to streamline the ``ananke`` pipeline, and to prevent the need for the user to manually handle the interface between ``Python`` and the ``C++`` backend software. It notably introduces dedicated wrapper submodules (hosted in repositories that are separate from that of ``py-ananke``, but linked as ``git`` submodules), namely ``py-EnBiD-ananke`` and ``py-Galaxia-ananke``, specifically developed to handle the installation and utilization of these ``C++`` subroutines, namely ``EnBiD`` [@EnBiD:2006;@EnBiDCode:2011] and a modified version of ``Galaxia`` [@Galaxia:2011;@GalaxiaCode:2011] called ``galaxia-ananke``. These submodules relieve users from the need to directly manage the ``C++`` software while isolating the ``C++`` wrapping process. This allows ``py-ananke`` to focus on processing inputs and outputs using pure ``Python``.

## ``py-EnBiD-ananke``

The full description of ``EnBiD`` is detailed in @EnBiD:2006, but to summarize, ``EnBiD`` uses a binary space partitioning tree to estimate the space density of a discrete data sample of particles given their coordinates in that space. The tree is recursively built by successively splitting spatial volumes in equally sample-populated volumic tree-nodes until each leaf node contains one single particle. The densities at the location of each particle are estimated using the volume of the leaf node that contains that particle and smoothed using kernel smoothing methods.

The ``py-EnBiD-ananke`` submodule handles the installation of ``EnBiD`` and interfaces with its pipeline. The installation pulls the archived source code of ``EnBiD`` from its SourceForge repository and builds its executable which gets added to the packaged data. Note that for this version of ``py-ananke``, the ``EnBiD`` pipeline is configured to determine 3D space densities for a set of particles, which ``py-ananke`` uses twice to get separate estimates of the position and velocity densities. In this situation, ``py-ananke`` combines both densities into a 6D phase space density, but future versions will consider the native implementation for determining true 6D phase space densities.

``py-EnBiD-ananke`` consists of a collection of functions that are combined into the pipeline-function ``enbid`` that takes particles 3D coordinates as input and returns their densities. The role of each sub-function is to write the files that are given as input to the ``EnBiD`` pipeline, to run the ``EnBiD`` pipeline and to read the pipeline's output files, for which various operational constants and templates are defined in a dedicated module file. 

## ``py-Galaxia-ananke``

The full description of ``Galaxia`` is detailed in @Galaxia:2011, but to summarize, ``Galaxia`` uses a given galactic model to generate a population of synthetic stars that composes it, with its associated astrometric and photometric catalog. The original pipeline had a more general purpose as the input galactic model can be generated via an N-Body simulation as much as it can be specified as a set of density distributions. However, for our purpose with our modified version ``galaxia-ananke``, the pipeline uses cosmological simulation star particle data provided by the user, specifically the mass, position, velocity, age, metallicity & abundances, as well as phase space densities for each star particle.

``galaxia-ananke`` generates the synthetic stars by sampling phase space to reproduce the distribution representing overlapping phase space kernels centered at each particle, invertly scaled with the particle density, and by sampling mass to reproduce a @Kroupa:2001 initial mass function. Each synthetic star carries the other properties of the parent particle such as age and metallicity, with which the masses are used to interpolate photometry from pre-computed isochrone tracks (details on those are described in the section [Dependencies]{label="Sec:Dependencies"}). Finally, astrometry is determined by converting the phase space coordinates to celestial coordinates given a user-specified observer phase space position.

The ``py-Galaxia-ananke`` submodule handles the installation of ``galaxia-ananke``, a modified version of ``Galaxia``, and interfaces with its pipeline. The ``galaxia-ananke`` source code lives in a separate repository which is linked as a ``git`` submodule in the repository of ``py-Galaxia-ananke``. At installation, ``py-Galaxia-ananke`` builds and packages the executable of ``galaxia-ananke`` from its source code directly from its ``git`` submodule, as well as the operational data for ``galaxia-ananke`` which includes the collections of isochrones sets. All the resulting ``galaxia-ananke`` packaged data is eventually placed in a dedicated cache folder that is created in the site-specific directory of the running ``Python`` installation.

``py-Galaxia-ananke`` consists of mainly three classes, with one function utilizing them to run the ``galaxia-ananke`` pipeline. It also includes a submodule that interfaces via dedicated objects with the data from the collection of isochrones sets/photometric systems. The three classes of ``py-Galaxia-ananke`` serve the following roles:

- ``Input`` objects are used to store the input star particles data, and have methods that write the input files that ``galaxia-ananke`` requires
- ``Survey`` objects receive ``Input`` objects and the selection of photometric systems to simulate, and have methods that run the ``galaxia-ananke`` pipeline and return ``Output`` objects
- ``Output`` objects serve as the main interface with ``galaxia-ananke``'s output files, and have methods that turn them into ``HDF5`` files and associated ``vaex`` dataframes

## ``py-ananke``

The implementation of ``py-ananke`` involves six classes, with only one - ``Ananke`` - being relevant to the end user:

- ``Ananke`` objects serve as the user interface, connecting all of ``py-ananke``'s classes and the ``py-Galaxia-ananke`` classes (described in the previous subsection) to execute the full pipeline via its method ``run``
- ``Universe`` objects store the particle data and various parameters provided to ``Ananke``
- ``Observer`` objects store the observing configuration, including the position in space
- ``DensitiesDriver`` objects utilize the particle data from the ``Universe`` class to compute and store phase space densities, employing ``py-EnBiD-ananke``
- ``ExtinctionDriver`` objects are utilized by ``Ananke`` objects for post-processing to estimate and append extinctions in the output catalogs of ``py-Galaxia-ananke``, only if the user specified dust column densities per star particle
- ``ErrorModelDriver`` objects are utilized by ``Ananke`` objects for post-processing to determine and append errors on the quantities in the output catalogs of ``py-Galaxia-ananke``

The latter two driver classes require respectively extinction coefficients and error models that are photometric-system-dependents and can be specified by the user. Also, ``py-ananke`` is designed with dedicated source files to contain default implementations, which currently only hold default for the Gaia photometric system. Future updates will continue to expand this further.

# Dependencies
\label{Sec:Dependencies}

``py-ananke`` makes use of the following ``Python`` packages:

- ``astropy`` [@astropy:2013;@astropy:2018;@astropy:2022]
- ``ebfpy`` [@ebfpy:2020]
- ``h5py`` [@h5py:2013]
<!-- - ``matplotlib`` [@matplotlib:2007] -->
- ``numpy`` [@numpy:2020]
- ``pandas`` [@pandas:2023]
<!-- - ``pytest`` [@pytest] -->
- ``scipy`` [@scipy:2020]
- ``vaex`` [@vaex:2018]

It also uses adapted versions of the ``C++`` packages:

- ``EnBiD`` [@EnBiD:2006;@EnBiDCode:2011] integrated in ``py-EnBiD-ananke``
- ``Galaxia`` [@Galaxia:2011;@GalaxiaCode:2011] integrated as ``galaxia-ananke`` in ``py-Galaxia-ananke``

Lastly, the ``galaxia-ananke`` ``C++`` submodule uses sets of pre-computed stellar isochrones generated by the Padova database[^1], using:

- PARSEC version 1.2S [@Bressan:2012;@Tang:2014;@Chen:2014;@Chen:2015] and COLIBRI PR16 [@Marigo:2013;@Rosenfield:2016] evolutionary tracks as in @Marigo:2017 (the solar metallicity is assumed to be 0.0152), with the mass-loss on the red giant branch using the Reimers formula with $\eta_{Reimers}=0.2$, and $\eta_{inTPC}=10$ for the resolution of the thermal pulse cycles in the COLIBRI section,
- specific choices of photometric systems for the corresponding instrument[^2] with OBC bolometric corrections as described in @Girardi:2002, @Girardi:2008 and @Marigo:2008,
- circumstellar dust compositions with a combination of 60% Silicate + 40% AlOx around O-rich M stars, and a combination of 85% AMC + 15% SiC around C-rich C stars, as in @Groenewegen:2006,
- periods from @Trabucchi:2019 and @Trabucchi:2021 for long-period variability during the red and asymptotic giant branch phases.

[^1]: [http://stev.oapd.inaf.it/cgi-bin/cmd](http://stev.oapd.inaf.it/cgbi-bin/cmd)
[^2]: further described in [http://stev.oapd.inaf.it/cmd/photsys.html](http://stev.oapd.inaf.it/cmd/photsys.html)

# Past and Ongoing Applications

@Sanderson:2020's data have now been in public use for 5 years and have delivered on the promise of this technique, leading to the discovery of a new stellar stream [@Necib:2020], the development and validation of new machine learning methods for inferring the origins of stars [@Ostdiek:2020], insights into the formation history of the MW [@Nikakhtar:2021], searches for dark matter subhalos [@Bazarov:2022], and inference of the MW's interstellar dust distribution [@Miller:2022].

In addition, a number of studies have also made use of the existing ``ananke`` pipeline that generated @Sanderson:2020's data, often through the extensive effort to adapt it to other photometric systems:

- @Shipp:2023 investigated the detectability of MW stellar streams in the Dark Energy Survey [@DES:2015;@DES:2018;@DES:2021], for which they produced mock star catalogs mimicking DECam photometry from disrupted star clusters identified around simulated MW-mass galaxies
- @Nguyen:2023 produced a synthetic survey mimicking the third data release of Gaia [@Gaia:2021;@Gaia:2023], similar to how @Sanderson:2020 produced a synthetic survey of the second data release of Gaia [@Gaia:2018]

These studies required significant effort caused by the challenges of using ``ananke``, which ``py-ananke`` is designed to alleviate. Current ongoing projects are already using the new ``py-ananke`` package, and are benefiting significantly from his ergonomicity.

# Author Contributions

As the lead developer on ``py-ananke``, ACRT adapted ``ananke`` by integrating its routines into a self-contained fully installable ``Python`` package, and implemented the new modular and object-oriented infrastructure ``py-ananke`` relies on, including the submodule ``py-EnBiD-ananke`` and ``py-Galaxia-ananke`` submodules, preparing all the associated repository overarching organization. RES, ``ananke``'s original developer, supervised ACRT throughout ``py-ananke``'s development and helped to disseminate early in-development versions of the software to collaborators. SS is the original developer of the ``C++`` softwares ``EnBiD`` and ``Galaxia`` which ``ananke`` relies heavily upon. APE tested the package for their own projects under the supervision of NGC. FN also tested the package for their projects and implemented fixes to the source code during testing. ACRT, NP and NGC added sets of isochrones to those in the ``galaxia-ananke`` ``C++`` submodule that had previously been assembled by RES.

# Acknowledgements

ACRT and RES acknowledge support from the Research Corporation through the Scialog Fellows program on Time Domain Astronomy, from NSF grant AST-2007232, from NASA grant 19-ATP19-0068, and from HST-AR-15809 from the Space Telescope Science Institute (STScI), which is operated by AURA, Inc., under NASA contract NAS5-26555.

Development of this code package made use of resources provided by the Frontera computing project at the Texas Advanced Computing Center (TACC). Frontera is made possible by National Science Foundation award OAC-1818253. Simulations used as test data for the package, and which form part of the example suite, were run using Early Science Allocation 1923870 and analyzed using computing resources supported by the Scientific Computing Core at the Flatiron Institute.  This work used additional computational resources from the University of Texas at Austin and TACC, the NASA Advanced Supercomputing (NAS) Division and the NASA Center for Climate Simulation (NCCS), and the Extreme Science and Engineering Discovery Environment (XSEDE), which was supported by National Science Foundation grant number OCI-1053575.

Package development and testing was performed in part at the Aspen Center for Physics, which is supported by National Science Foundation grant PHY-1607611, and at the Kavli Insitute for Theoretical Physics workshop "Dynamical Models for Stars and Gas in Galaxies in the Gaia Era" and the 2019 Santa Barbara Gaia Sprint, supported in part by the National Science Foundation under Grant No. NSF PHY-1748958 and by the Heising-Simons Foundation. 

The authors are grateful to Anthony Brown and Jos de Bruijne for their cooperation in building the Gaia error models encoded in this package. We also gratefully acknowledge the input and encouragement of the many participants of the Gaia Sprints (2017--2019), and of the Gaia Challenge series (2012-2019).

The authors thank the extended [Galaxy Dynamics @ UPenn group](http://web.sas.upenn.edu/dynamics/) and the attendees of the "anankethon" workshops for the valuable feedback and suggestions they provided which have contributed to the refinement and enhancement of the package.


# References
