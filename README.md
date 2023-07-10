# py-ananke

Welcome to Py-ananke! It is a powerful Python package that offers ananke, a comprehensive pipeline designed to generate mock astrometric and photometric catalogs of synthetic stars derived from particle-based simulated star populations.

## Project genesis

![GAIA mock star survey from FIRE](https://web.sas.upenn.edu/dynamics/files/2021/02/galactic-map-m12f-lsr-1-threecolor-medfilt-16x9-1.png)

The package was designed to provide easy installation and distribution of the ananke software, as described in [Sanderson et al. 2020](https://ui.adsabs.harvard.edu/abs/2020ApJS..246....6S/abstract). In this work, the team focused on cosmological simulations, such as the latte suite of FIRE simulations which have limited resolution and cannot accurately represent fully resolved stellar populations with individual stars. To address this challenge, the authors of ananke developed a framework consisting of scripts and data that enabled the generation of synthetic GAIA star surveys from these simulated galaxies. The framework combines density estimations and IMF sampling techniques to create representative populations of mock stars.

An essential aspect of ananke is its integration with the [EnLink](https://ui.adsabs.harvard.edu/abs/2009ApJ...703.1061S/abstract)/[EnBiD](http://ascl.net/1109.012) C++ software for computing phase space densities. These computed densities are then used as input for the [Galaxia](http://ascl.net/1101.007) C++ software, which generates synthetic surveys by incorporating user-supplied GAIA isochrones to produce the mock photometry.

The development of py-ananke aims to make this sophisticated framework accessible to a broader community. By providing a self-contained and easily installable Python package, we strive to facilitate the usage and adoption of ananke for generating mock star surveys from cosmological simulations, enabling the investigation of stellar halos around nearby galaxies.

## Getting started

Py-ananke is compatible with Python versions above 3.7.12 and below 3.11. The project is organized into three branches: [main](https://github.com/athob/py-ananke/tree/main), [stable](https://github.com/athob/py-ananke/tree/stable), and [develop](https://github.com/athob/py-ananke/tree/develop). The main branch contains the latest released version, while the stable and develop branches host versions currently in development, with stable being the most recent stable version. Py-ananke uses dedicated wrapper submodules, namely [py-EnBiD-ananke](https://github.com/athob/py-EnBiD-ananke) and [py-Galaxia-ananke](https://github.com/athob/py-Galaxia-ananke), specifically developed to handle the installation and utilization of the C++ backend software, [EnBiD](http://ascl.net/1109.012), and a modified version of [Galaxia](http://ascl.net/1101.007) called [Galaxia-ananke](https://github.com/athob/galaxia-ananke). These submodules relieve users from the need to directly manage the C++ software while isolating the C++ wrapping process. This allows py-ananke to focus on processing inputs and outputs using pure Python. It is worth noting that [Galaxia-ananke](https://github.com/athob/galaxia-ananke) incorporates several pre-installed photometric systems, represented by sets of isochrones generated from the [CMD web interface](http://stev.oapd.inaf.it/cgi-bin/cmd) (commonly referred to as Padova isochrones). Among the available options are HST, GAIA, Euclid, Rubin, JWST & Roman.

### Installation

To install py-ananke, you can use the following pip command, which pulls the latest version directly from the repository's main branch:

    pip install git+https://github.com/athob/py-ananke@main

Alternatively, if you prefer, you may clone the repository to your local machine and then install py-ananke using the following pip command, which installs it from your local copy of the repository:

    git clone https://github.com/athob/py-ananke
    cd py-ananke
    pip install .

Please note that the command with flag `pip install . --no-cache-dir` may be necessary due to some dependencies issues.

### Simplified use case

The repository includes a Jupyter notebook that demonstrates a simplified use case utilizing a dummy set of randomly generated particle data. You can access the notebook directly at [jupyter/testing_ananke.ipynb](jupyter/testing_ananke.ipynb). This notebook provides a step-by-step example to help you understand the functionality and usage of py-ananke in a straightforward manner.

## On-going development

Py-ananke has recently entered its beta phase, and we are diligently working towards its submission to the [Journal of Open Source Software](https://joss.theoj.org).

### Upcoming updates

We have an exciting roadmap of upcoming updates planned, which we aim to implement prior to or following the submission. Here are some of the planned updates in no particular order:

- **Improving Extinction**: The extinction feature is currently in an experimental state, and we have identified areas for significant improvement. Firstly, while the user can supply their own extinction coefficients Aλ/A0 for any photometric system, only GAIA currently has default coefficients. Future updates will expand the range of default extinction coefficients for different systems. Secondly, the estimation of dust column density maps per particle currently requires user input. Our plan is to incorporate a treatment that directly computes dust column densities from the simulated metal-enriched gas provided by the user.
- **Implementing Error Modelling**: The original ananke framework ([Sanderson et al. 2020](https://ui.adsabs.harvard.edu/abs/2020ApJS..246....6S/abstract)) featured error modelling as a significant component. In future updates, we will introduce a framework that allows for the incorporation of simple error models into the pipeline, enhancing the robustness of the generated mock surveys.
- **Interfacing with Isochrone Databases**: Py-ananke currently includes pre-loaded isochrones for a chosen photometric system (some of which are listed in the introduction section). Our plan is to implement a direct interface with established isochrone databases such as [Padova](http://stev.oapd.inaf.it/cgi-bin/cmd) or [MIST](https://waps.cfa.harvard.edu/MIST/), enabling users to download available photometric systems on-the-fly. Additionally, we aim to develop a framework that allows py-ananke to output photometry in a range of commonly used calibration standards.
- **Additional Modularization**: While [EnBiD](http://ascl.net/1109.012) serves as the density estimation routine of choice, we plan to expand the options by adding more choices such as [EnLink](https://ui.adsabs.harvard.edu/abs/2009ApJ...703.1061S/abstract). Furthermore, we intend to diversify the selection of kernel functions for density estimation and sampling mock stars in phase space, making it possible to utilize anisotropic kernel functions. Additionally, we will enhance the flexibility of py-ananke by incorporating a wider range of initial mass functions (IMFs) and allowing mass sampling based on present mass functions, particularly for generating mock stars in globular clusters.
- **Quality of Life Updates**: We are dedicated to enhancing the user experience and overall usability of py-ananke. To that end, we will be implementing various quality of life updates, refining the software interface, improving documentation, and streamlining the overall workflow.

These upcoming updates signify our commitment to continuously improve py-ananke and address the evolving needs of the community. We encourage users to stay engaged with the project, provide feedback, and contribute to its development as we work towards a more comprehensive and user-friendly tool for generating mock surveys.

### Contributing

The entire py-ananke software code is released under the open-source [GPL3.0 licence](LICENCE), ensuring its accessibility and transparency. You can readily access the code in this main GitHub repository, as well as its submodules repositories. We encourage users to utilize the [Github issues](https://github.com/athob/py-ananke/issues) feature to report any bugs encountered or suggest new ideas for improvement. Contributions to the project are highly valued and greatly appreciated. To contribute, we kindly request that you make your changes in a separate branch or fork of the repository. Once your contributions are ready, you can submit a [pull request](https://github.com/athob/py-ananke/pulls) to merge them into the [develop](https://github.com/athob/py-ananke/tree/develop) branch.


## Acknowledgements

We extend our sincere gratitude to [Robyn Sanderson (UPenn)](https://live-sas-physics.pantheon.sas.upenn.edu/people/standing-faculty/robyn-sanderson), [Andrew Eden (FloridaTech)](mailto:Andrew%20Eden%20<aeden2019@my.fit.edu>), [Nondh Panithanpaisal (UPenn/CarnegieObs)](https://nonsk131.github.io), and [Nicolas Garavito-Camargo (FlatironCCA)](https://jngaravitoc.github.io/Garavito-Camargo/) for their invaluable contributions and support during the development of this package. Their expertise, guidance, and collaboration have been instrumental in shaping the vision and advancement of this project. We also appreciate the valuable feedback and suggestions provided by the wider community, including the extended [Galaxy Dynamics @ UPenn group](web.sas.upenn.edu/dynamics/) and the participants of the "anankethon" workshop, which have significantly contributed to the refinement and enhancement of the package.
