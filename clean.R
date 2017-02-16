# Load libraries
library(tidyverse)
library(stringr)
library(lubridate)

setwd("/Users/Josiah/Dropbox/GitHub/boston-crash-modeling")


# Function can be found on my github: https://github.com/JosiahParry/general_R/blob/master/personal_functions/list_dat_dirs.R
list_dat_dirs <- function(dir, extension = "RAW", case_sensitive = FALSE) {
  case_sensitive <- ifelse(case_sensitive == TRUE, FALSE, TRUE)
  list.dirs(dir)[str_detect(list.dirs(dir),
                            fixed(extension, ignore_case = case_sensitive))]
}

# https://github.com/JosiahParry/general_R/blob/master/personal_functions/read_multiple_csv.R
read_multiple_csv <- function(dat_dirs, skip = 0) {
    all_files <- list()
    for (i in 1:length(dat_dirs)) {
      for (j in 1:length(list.files(dat_dirs[i]))) {
        all_files[length(list.files(dat_dirs[1:i])) - (length(list.files(dat_dirs[i])) - j)] <- 
          list(read_csv(file.path(dat_dirs[i],list.files(dat_dirs[i])[j]),
                        skip = skip))
      }
    }
    bind_rows(all_files)
}

# Read in all files 
crashes <- read_multiple_csv(list_dat_dirs(getwd()))

# Clean column names 
colnames(crashes) <- colnames(crashes) %>% 
  str_replace_all("[:punct:]", "_") %>%
  str_replace_all(" ", "_") %>%
  tolower()

crashes <- crashes %>%
  mutate(city = str_split_fixed(city_town_name, " ", 2)[, 1], 
         # Split city_town_name, second split is the town surrounded by (), first is city
         town = str_split_fixed(city_town_name, " ", 2)[, 2] %>%
           str_replace_all("\\(", "") %>% 
           str_replace_all("\\)", ""),
    crash_date = dmy(crash_date),
    crash_time = hm(crash_time),
    date_time = ymd_hms(paste(crash_date, crash_time))) %>%
  # Split fields by vehicle number
  mutate(vehicle_action_prior_to_crash = str_split(vehicle_action_prior_to_crash, " \\/ "),
         vehicle_travel_directions = str_split(vehicle_travel_directions, " \\/ "),
         most_harmful_events = str_split(most_harmful_events, " \\/ "),
         vehicle_configuration = str_split(vehicle_configuration, " \\/ ")) %>%
  unnest() %>%
  # Add vehicle number
  mutate(vehicle_number = str_extract(vehicle_configuration, "[0-9]+")) %>%
  # Remove Vehicle number (V#)
  mutate(vehicle_action_prior_to_crash = str_replace(vehicle_action_prior_to_crash, "V[0-9]+:", "") %>%
           str_trim(),
         vehicle_travel_directions = str_replace(vehicle_travel_directions, "V[0-9]+:", "") %>%
           str_trim(),
         most_harmful_events = str_replace(most_harmful_events, "V[0-9]+:", "") %>%
           str_trim(),
         vehicle_configuration = str_replace(vehicle_configuration, "V[0-9]+:", "") %>%
           str_trim()) %>%
  # Split non motorists to 1 per row
  mutate(non_motorist_type = str_split(non_motorist_type, " \\/ ")) %>%
  unnest() %>%
  # Add non-motorist numbers
  mutate(non_motorist_number = str_extract(non_motorist_type, "[0-9]+")) %>%
  # Remove non-motorist number
  mutate(non_motorist_type = str_replace(non_motorist_type, "P[0-9]+:", ""))








