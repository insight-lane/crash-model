| Feature Name | Description | Example Values | City |Comments (Optional) |
| ---: | ---: | ---: | ---: |---: |
| segment\_id | Id of segment in question | 26 | All |   |
| Surface\_Tp | 1 = Unimproved graded earth, or soil surface road<br/> 2 = Gravel or stone road<br/> 3 = Brick road<br/> 4 = Block road<br/>5 = Surface-treated road<br/> 6 = Bituminous concrete road<br/> 7 = Portland cement concrete road<br/> 8 = Composite road; flexible over rigid<br/>9 = Composite road; rigid over flexible or rigid over rigid<br/> (&quot;white topping&quot;) 10=Stone dust | 5 |   Boston |Categorical, a column is made for each unique value of this in the dataset |
| SPEEDLIMIT | Speed limit for that segment | 20 | Boston  | Categorical, a column is made for each unique value of this in the dataset |
| volume_coalesced | Total Volume of vehicles passing that segment, inclusing heavyweight, lightweight and bikes. Final values are after processing ATR data in our pipeline to impute missing continuous values using the k-NN algorithm. | 2045 | Boston |  |
| speed_coalesced | Mean speed (in mph) of vehicles passing that segment. Final values are after processing ATR data in our pipeline to impute missing continuous values using the k-NN algorithm. | 22 | Boston |  |
| Lanes | Number of lanes in the segment | 3 | All  |   |
| width | Width of the road segment, as given by open street map | 15 | All  | Used as a log value in our model  |
| Struct\_Cnd |  Structural Condition | &#39;pre\_month&#39; |  Boston | Categorical, a column is made for each unique value of this in the dataset |
| cycleway_type |0 = None<br/> 1 = Lane<br/> 2 = Shared Labe<br/> 3 = Track<br/>4 = Shared busway<br/> 5 = Buffered Lane<br/> | 0 | All |   |
| F\_F\_Class| Federal Functional class for that segment. Codes includes:<br/>1 = Interstate<br/> 2 = Other<br/> Freeways and Expressways<br/> 3 = Other Principal Arterial<br/> 4 = Minor Arterial<br/> 5 = Major Collector<br/> 6 = Minor Collector<br/> 7 = Local<br/> | 5 | Boston|Functional classification is the grouping of highways, roads and streets by the character of service they provide and was developed for transportation planning purposes. Categorical, a column is made for each unique value of this in the dataset |
| Conflict | | | |   |
| oneway | Is the segment one way or not | 0 | All |Boolean |
| AADT | Annual average daily traffic value on that segment for that week | 10.008883 | Boston| Used in our model as a log transformed value |
| visionzero | Number of vision zero comments from seeclickfix for that segment | 5 | Boston  |   |
| Seeclickfix | Number of concerns from seeclickfix for that [week, year] | 10 |Currently in use for Cambridge only  |   |
| parking_tickets | Number of parking tickets for that segment | 10 |Currently in use for Cambridge only  |   |
| intersection | Is this segment part of an intersection | 0/1 |All|   |
| log_width_per_lane | Log value of width | |All|   |
