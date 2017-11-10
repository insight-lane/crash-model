
# To run the script, insert an api key from Wunderground below:

apikey <- ""

library(jsonlite) #for parsing json output (fromJSON function)
library(plyr)

#Extract data for Jan-01 and then append daily weather data for Boston, 2016 to this dataset
url <- "http://api.wunderground.com/api/api_key/history_20160101/q/MA/Boston.json"
data <- fromJSON(txt = url)

data <- as.data.frame(data$history$dailysummary)
data$dateFull <- data$date$pretty
data <- data[,2:71] #extract out the nested date dataframe that carries same information as data$date$pretty

for (month in 1:12)
{
  if (nchar(month) != 2)
  {
    month <- paste("0",month,sep="")
  }
  #separating months with 31 days from 30 and 29
  if (month == "01" | month == "03" | month == "05" | month == "07" | 
        month == "08" | month == "10" | month == "12") 
  {
    for (day in 1:31)
    {
      if (nchar(day) != 2)
      {
        day <- paste("0",day,sep="")
      }
      url <- paste("http://api.wunderground.com/api/api_key/history_2016",month,day,"/q/MA/Boston.json",sep="")
      data2 <- fromJSON(txt = url)
      data2 <- as.data.frame(data2$history$dailysummary)
      data2$dateFull <- data2$date$pretty
      data2 <- data2[-1]
      data <- rbind(data, data2)
    }
  }
  else if (month == "02") #accounting for february as leap
  {
    for (day in 1:29)
    {
      if (nchar(day) != 2)
      {
        day <- paste("0",day,sep="")
      }
      url <- paste("http://api.wunderground.com/api/api_key/history_2016",month,day,"/q/MA/Boston.json",sep="")
      data2 <- fromJSON(txt = url)
      data2 <- as.data.frame(data2$history$dailysummary)
      data2$dateFull <- data2$date$pretty
      data2 <- data2[-1]
      data <- rbind(data, data2)
    }
  }
  else
  {
    for (day in 1:30)
    {
      if (nchar(day) != 2)
      {
        day <- paste("0",day,sep="")
      }
      url <- paste("http://api.wunderground.com/api/77655c0d74f69756/history_2016",month,day,"/q/MA/Boston.json",sep="")
      data2 <- fromJSON(txt = url)
      data2 <- as.data.frame(data2$history$dailysummary)
      data2$dateFull <- data2$date$pretty
      data2 <- data2[-1]
      data <- rbind(data, data2)
    }
  }
}

data <- data[-1,] #remove duplicate January 1st observation
data <- plyr::rename(data, replace = c("dateFull" = "date")) #rename date variable
weatherBoston <- data
save(weatherBoston, file = "BostonWeather2016_Wunderground.Rda")
write.csv(weatherBoston, file = "BostonWeather2016_Wunderground.Rda")
