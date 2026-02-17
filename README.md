Flight Path Optimization Framework (LNM)
This repository contains the experimental environment developed for my Bachelor's Thesis: "Development of an experimental environment for the automatic analysis and optimization of flight paths with Little Navmap".

Concept: The Simulator
The system utilizes Little Navmap as an "Evaluation Simulator." Python-based algorithms (Dijkstra, A*, K-SP) generate route proposals that are automatically sent to LNM to retrieve realistic fuel and time metrics based on aircraft performance profiles (.lnmperf).

Installation (WSL/Ubuntu)
Clone the repository: git clone https://github.com/your-username/FlightPlanning.git

Run the installer: bash setup_env.sh

Ensure Little Navmap is installed and its web server is active on port 8965.

Case Study: LEMD-UUEE
The environment includes validation using Eurocontrol Ground Truth data (December 2019), filtering 61 real flights between Madrid and Moscow from a massive dataset of 747,469 records.


### Data Acquisition
Due to the significant size of the raw datasets and processed navigation files (approx. 12Gb), the complete `data/` folder is hosted externally on Google Drive. 

You can download the dataset here: [Download Data Folder](https://drive.google.com/file/d/1cGn7C6QIrA0i6AODXKc8muHZvQcupUSJ/view?usp=sharing)

**Note:** Access is restricted to maintain data integrity and project tracking. Please **request access** through the link. Once granted and downloaded, extract the contents and place them directly into the `/data` directory in the root of this repository to ensure all scripts function correctly.