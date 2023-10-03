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
affiliations:
 - name: Department of Physics & Astronomy, University of Pennsylvania, 209 S 33rd Street, Philadelphia, PA 19104, USA 
   index: 1
 - name: Department of Aerospace, Physics and Space Sciences, Florida Institute of Technology, Melbourne, FL 32901, USA
   index: 2
 - name: Department of Physics, Yale University, New Haven, CT 06511, USA
   index: 3
 - name: The Observatories of the Carnegie Institution for Science, 813 Santa Barbara Street, Pasadena, CA 91101, USA
   index: 4
 - name: TAPIR, California Institute of Technology, Pasadena, CA 91125, USA
   index: 5
 - name: Center for Computational Astrophysics, Flatiron Institute, Simons Foundation, 162 Fifth Avenue, New York, NY 10010, USA
   index: 6
date: 1 October 2023
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
# aas-doi: ?
# aas-journal: ?
---

# Summary

We find ourselves on the brink of an exciting era in observational astrophysics, driven by groundbreaking facilities like JWST, Euclid, Rubin, Roman, SKA, and ELT. Simultaneously, computational astrophysics has made significant strides, yielding highly realistic galaxy formation simulations, thanks to both hardware and software enhancements. Bridging the gap between simulations and observations has become paramount for meaningful comparisons.

We introduce ``py-ananke``, a Python pipeline designed to generate synthetic star catalogs from cosmological simulations, adaptable to various instruments. Building upon its predecessor, ``ananke`` by @Sanderson:2020, which produced GAIA mock star surveys, the ``py-ananke`` package offers a user-friendly "plug & play" experience. The pipeline employs cutting-edge phase-space density estimation and initial mass function sampling to convert particle data into synthetic stars, while interpolating pre-computed stellar isochrone tracks for photometry. Additionally, it includes modules for estimating interstellar reddening, dust-induced extinctions, and for quantifying errors through dedicated modeling approaches. ``py-ananke`` promises to serve as a vital bridge between computational astrophysics and observational astronomy, facilitating preparations for the next generation of telescopes.


# Statement of need

The upcoming decade holds promise for groundbreaking discoveries, thanks to a multitude of recent and forthcoming observational facilities. The James Webb Space Telescope [@JWST:2006], for instance, with its exceptional specifications, has already delved into early universe galaxies with unprecedented detail, revealing their rich diversity [@Ferreira:2022;@Adams:2023;@Finkelstein:2023;@Kocevski:2023;@Kartaltepe:2023;@PerezGonzalez:2023;@Harikane:2023;@Hsiao:2023;@Trussler:2023;@Casey:2023;@Ferreira:2023;@Eisenstein:2023]. The recently launched Euclid Telescope [@Euclid:2011] promises to shed light on the universe's accelerating expansion by surveying an immense number of galaxies [@EuclidCollaboration:2022]. The Vera Rubin Observatory [@Rubin:2019], with first light expected soon, will precisely map the Milky Way and beyond, providing exceptional stellar astrometry data. Furthermore, the Nancy Grace Roman Space Telescope [@Roman:2019], set to launch in the next couple of years, will offer a wide field of view for deep-sky near-infrared exploration, facilitating the study of resolved stellar populations in nearby galaxies [@Dey:2023;@Han:2023]. However, these observatories will generate an unprecedented amount of raw data, necessitating community preparedness.

In parallel, a number of projects have emerged over the last decade in computational astrophysics, continuously surpassing hardware and software limits   to simulate galaxy formation in a cosmological context realistically [@Stinson:2010;@Stinson:2013;@Hirschmann:2014;@Dubois:2014;@Vogelsberger:2014;@Hopkins:2014;@Schaye:2015;@Crain:2015;@Khandai:2015;@Wang:2015;@Dolag:2015;@Dolag:2016;@Feng:2016;@Dave:2016;@Tremmel:2017;@Nelson:2018;@Pillepich:2018;@Springel:2018;@Henden:2018;@Hopkins:2018;@Pfeffer:2018;@Kruijssen:2019;@Peeples:2019;@Dave:2019;@Bastian:2020;@Dubois:2021;@Applebaum:2021;@Hopkins:2023;@Feldmann:2023;@Schaye:2023;@Pakmor:2023]. These simulations serve as invaluable test beds for tools developed in anticipation of the next-generation telescope era, but also for our own models. However, translating these simulations into mock observables is challenging due to the representation of stellar populations as star particles, with each particle representing between $10^4$ to $10^8$ times the mass of the Sun worth of stars. To compare simulations with real data, one must break down these particles into individual stars consistently.

This challenge was addressed by @Sanderson:2020 when producing a mock GAIA catalog from Milky-Way-like simulated galaxies in the latte suite of FIRE simulations [@Wetzel:2016] using the so-called ``ananke`` pipeline. They used phase-space density estimation and initial mass function sampling to transform particle data into individual synthetic stars, retaining parent particle age and metallicity. Photometry was determined by interpolating pre-computed stellar isochrone tracks from the Padova database [@Marigo:2017] based on star mass, age, and metallicity. Additional post-processing included estimating interstellar reddening, per-band dust extinctions using metal-enriched gas distribution, and error quantification based on a model described by functions calibrated to [@Gaia:2018] characterizations.

The ``ananke`` pipeline by @Sanderson:2020, though powerful, lacks user-friendliness and flexibility. It is challenging to integrate into other pipelines and expand beyond the GAIA photometric system. The development of ``py-ananke`` aims to make this framework more accessible to a wider community. By providing a self-contained and easily installable Python package, it streamlines the ``ananke`` pipeline, automating tasks previously requiring manual intervention. ``py-ananke`` also expands ``ananke``'s photometric system support and employs a modular implementation for future enhancements. It promises a smoother upgrade path for users.

# Code description



# Dependencies citations

``py-ananke`` makes use of the following Python packages:

- astropy [@astropy:2013;@astropy:2018;@astropy:2022]
- ebfpy [@ebfpy:2020]
- h5py [@h5py:2013]
<!-- - matplotlib [@matplotlib:2007] -->
- numpy [@numpy:2020]
- pandas [@pandas:2023]
<!-- - pytest [@pytest] -->
- scipy [@scipy:2020]
- vaex [@vaex:2018]

It also uses adapted versions of the ``C++`` packages:

- EnBiD [@EnBiD:2011] in ``py-EnBiD``
- Galaxia [@Galaxia:2011] as ``galaxia-ananke`` in ``py-Galaxia-ananke``

Lastly, the ``galaxia-ananke`` ``C++`` submodule uses sets of pre-computed stellar isochrones generated by the Padova database[^1], using:

- PARSEC version 1.2S [@Bressan:2012;@Tang:2014;@Chen:2014;@Chen:2015] and COLIBRI PR16 [@Marigo:2013;@Rosenfield:2016] evolutionary tracks as in @Marigo:2017, with mass-loss on the red giant branch using the Reimers formula with $\eta_{Reimers}=0.2$, and $\eta_{inTPC}=10$ for the resolution of the thermal pulse cycles in the COLIBRI section,
- specific choices of photometric systems for the corresponding instrument[^2] with OBC bolometric corrections as described in @Girardi:2002, @Girardi:2008 and @Marigo:2008,
- circumstellar dust compositions with a combination of 60% Silicate + 40% AlOx around O-rich M stars, and a combination of 85% AMC + 15% SiC around C-rich C stars, as in @Groenewegen:2006,
- periods from @Trabucchi:2019 and @Trabucchi:2021 for long-period variability during the red and asymptotic giant branch phases.

[^1]: [http://stev.oapd.inaf.it/cgi-bin/cmd](http://stev.oapd.inaf.it/cgi-bin/cmd)
[^2]: further described in [http://stev.oapd.inaf.it/cmd/photsys.html](http://stev.oapd.inaf.it/cmd/photsys.html)

# Past and ongoing applications



# Author Contributions



# Acknowledgements


# References