Crash Modeling
===================

Outline:
-----------------------
 - Project Overview
 - Data Sources and Modelling
 - Getting Started
 - Connect with us
 - Project Organization

Project Overview
-----------------------

**Motivation**

This project was originally begun as a collaboration between Data4Democracy and the City of Boston.

On Jan 25th, 2017, [9 pedestrians were hit in Boston by vehicles](http://www.bostonherald.com/news/local_coverage/2017/01/battle_for_safer_streets_nine_pedestrians_hit_in_boston_in_1_day). While this was a particularly dangerous day, there were 21 fatalities and over 4000 severe injuries due to crashes in 2016 alone, representing a public health issue for all those who live, work, or travel in Boston. The City of Boston would like to partner with Data For Democracy to help develop a dynamic prediction system that they can use to identify potential trouble spots to help make Boston a safer place for its citizens by targeting timely interventions to prevent crashes before they happen.

This is part of the City's long-term [Vision Zero initiative](http://www.visionzeroboston.org/), which is committed to the goal of zero fatal and serious traffic crashes in the city by 2030. The Vision Zero concept was first conceived in Sweden in 1997 and has been widely credited with a significant reduction in fatal and serious crashes on Sweden’s roads in the decades since then. Cities across the United States are adopting bold Vision Zero initiatives that share these common principles.

> Children growing up today deserve...freedom and mobility. Our seniors should be able to safely get around the communities they helped build and have access to the world around them. Driving, walking, or riding a bike on Boston’s streets should not be a test of courage.
>
> — Mayor Martin J. Walsh


**What is the goal of the project?**

The goal of the project is to promote the development of safer roads by identifying areas of high risk in a city's road network. It seeks to support the decision-making of transportation departments in 3 ways:

1. Identify high risk locations - which roads in the network represent the greatest risk of crashes?

2. Explain the contributing factors of risk - what are the features, patterns and trends that result in a location having elevated risk?

3. Assess the impact of intervention - what is the effect of a past or planned intervention on the risk of crashes?

**Who are the intended users of the project?**

Though originally a collaboration between Data4Democracy and the City of Boston, the project is now being developed to work for any city that wishes to use it. The intended users include city transportation departments, those responsible for managing risk on road networks and individuals interested in crash risk.


**How does the project achieve its goal?**

The project uses machine learning to generate predictions of risk by combining various types of data. Right now it makes use of:

- road segment data to build a map of a city's road network, presently being sourced from [OpenStreetMap](https://www.openstreetmap.org/)

- historical crash data to determine which locations have proved high risk in the past, provided by participating cities through their open data portals

- safety concerns data to understand where citizens believe their roads are unsafe and the nature of their concerns, also provided by participating cities by way of their respective VisionZero programs or [SeeClickFix](https://seeclickfix.com/)

Future versions of the project are likely to make use of:

- traffic volume data to understand which roads experience the highest traffic and how changing trends of usage might affect risk

- more detailed road features including speed limits, signals, bike lanes, crosswalks, parking etc.

- road construction data

Predictions are generated on a per road-segment basis and will be made available via a searchable web visualization, with roads of highest risk easily identifiable. Details of which factors are most associated with risk on each road will also be included.

**What are the requirements for use?**

Any city that wishes to can make use of the project. At a minimum, geo-coded historical crash data is required. Beyond this, cities that can supply safety concerns data (VisionZero or otherwise) will be able to generate more advanced predictions of risk.

**What is the release schedule?**

The intended roadmap of development for the project can be found at [https://github.com/Data4Democracy/crash-model/projects](https://github.com/Data4Democracy/crash-model/projects).

**How can I access the project?**

This repo can be downloaded and run in its entirety using Docker, or you can see a current deployment of the project at [https://insightlane.org](https://insightlane.org).


Data Sources and Modelling
-----------------------
### Data Sources
-	[Open street maps network and features](https://wiki.openstreetmap.org/wiki/Map_Features)
-	Crash data must be provided (see data standards)
-	Pipeline can incorporate other networks and features (see using custom data sources)
-	All our processed data is in a private repository in data.world -- ping a project lead or maintainer on Slack to get access. More detailed documentation is contained there.


### Data Model 
-	The [data dictionary](https://github.com/Data4Democracy/crash-model/blob/master/docs/model_data_dictionary.md) contains information about the default features included in the model 
-	As of V2.0, the models tests [Logistic Regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) vs [XGBoost](https://xgboost.readthedocs.io/en/latest/python/python_api.html#xgboost.XGBClassifier) and picks the best performing (based on [ROC AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html))

Getting Started
-----------------------
## Setting up

### Dependencies:
Most of the work on this project so far has been done in Python, in Jupyter notebooks.
- Python 3.6 (we recommend [Anaconda](https://www.continuum.io/downloads))
- conda (included with Anaconda)

### Module Dependencies
If using conda, you can get all the depencies using the [environment_linux.yml](https://github.com/Data4Democracy/crash-model/blob/master/environment_linux.yml), [environment_mac.yml](https://github.com/Data4Democracy/crash-model/blob/master/environment_mac.yml), or [environment_pc.yml](https://github.com/Data4Democracy/crash-model/blob/master/environment_pc.yml) files.
Python modules: Use requirements\_spatial.txt


rtree additionally requires download and installation of [libspatialindex](http://libspatialindex.github.io/)
(For Anaconda install, can use [conda-forge](https://anaconda.org/conda-forge/libspatialindex))


### Environment:
You'll want to reproduce the packages and package versions required to run code in this repo, ideally in a virtual environment to avoid conflicts with other projects you may be working on. We have a version of environment.yml without versions, but recommend you use the pinned version for your operating system (environment_linux.yml, environment_mac.yml, or environment_pc.yml) since they shouldn't break if newer conda packages break).

    $ conda env create -f [environment_linux.yml or other environment file]
    $ activate crash-model


### Docker:
A basic [Docker](https://www.docker.com) image has been created to run the project in a container, using the ContinuumIO miniconda3 base image (Python 3.6). The virtual environment 'crash-model' is installed and activated when the image is started via container, as well as an apache2 webserver via supervisord to serve the visualization.

You can download the latest stable image from D4D's Docker Hub repo by running the following command, from a machine with the Docker engine installed:

	$ docker pull datafordemocracy/crash-model:latest

Automatic building of images from the project's GitHub project have been configured to run on every commit to a branch. To see all available tagged versions of the image and their date of creation, see [https://hub.docker.com/r/datafordemocracy/crash-model/tags/](https://hub.docker.com/r/datafordemocracy/crash-model/tags/)

For testing purposes you can build the image yourself from the Dockerfile by running the following from within the project repo:

	$ docker build --tag datafordemocracy/crash-model:[tag] .

Once you have the image, you can run it in a container. The project folder (/app) is intentionally empty within the image, so you'll also need the project repo from GitHub available on your local machine. To do this run:

	$ docker run -d -p 8080:8080 --name bcm.local -v /local/path/to/project_repo:/app datafordemocracy/crash-model:[tag]

The arguments to this command perform the following:

1. `-d` detaches the container and runs it in the background (gives you your shell back)
2. `-p 8080:8080` maps port 8080 from the container to 8080 on your local machine (required if you want to view the visualization via browser)
3. `--name bcm.local` names the container 'bcm.local' (or whatever value you specify)
4. `-v /local/path/to/project_repo:/app` mounts your local machine's copy of the project repo into /app in the container.

Once you have a running container, you can get a shell on it to run the pipeline, test scripts etc. by running:

	$ docker exec -it bcm.local /bin/bash


## Contributing
"First-timers" are welcome! Whether you're trying to learn data science, hone your coding skills, or get started collaborating over the web, we're happy to help. If you have any questions feel free to pose them on our [Slack channel](https://datafordemocracy.slack.com/messages/p-crash-model), or reach out to one of the team leads. If you have questions about Git and GitHub specifically, our github-playground repo and the #github-help Slack channel are good places to start.


**I want to know what’s going on and pick up a task I like**
-	Open tasks are available [here](https://github.com/Data4Democracy/crash-model/issues)
-	Issues pertaining towards upcoming releases are available [here](https://github.com/Data4Democracy/crash-model/projects)


**I want to add a new city**
-	See instructions in src README

**I want to add a new city to our showcase**
-	Link to onboard showcase


Connect with us
-----------------------
Join our [Slack channel](https://datafordemocracy.slack.com/messages/p-crash-model) on the D4D Slack. If you haven't joined our Slack yet, fill out [this contact form](https://www.datafordemocracy.org/join-us)!

Leads:
 - [@bpben](https://datafordemocracy.slack.com/messages/@bpben)
 - [@j-t-t](https://datafordemocracy.slack.com/messages/@j-t-t)
 - [@alicefeng](https://datafordemocracy.slack.com/messages/@alicefeng)
 - [@terryf82](https://datafordemocracy.slack.com/messages/@terryf82)


Project Organization
-----------------------

    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py

<p><small>Project structure based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
