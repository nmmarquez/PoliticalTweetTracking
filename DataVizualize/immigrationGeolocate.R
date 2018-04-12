rm(list = ls())
library(httr)
library(jsonlite)
library(dplyr)

orskey <- read.table("~/.openrouteservicetoken", stringsAsFactors=F)$V1
ghkey <- read.table("~/.graphhopperkey", stringsAsFactors=F)$V1

DFLocs <- read.csv("~/Downloads/locationTweets.csv", stringsAsFactors=FALSE)
DFUniqueLocs <- unique(DFLocs)
row.names(DFUniqueLocs) <- NULL
bsearch <- paste0("https://nominatim.openstreetmap.org/",
                  "search?city=%c%&state=%s%&format=json")

DFLocMatch <- data.frame()

for(i in 1:nrow(DFUniqueLocs)){
    term <- DFUniqueLocs$location[i]
    termsplit <- strsplit(term, ",") %>% unlist
    city <- gsub(" ", "+", termsplit[1])
    state <- gsub(" ", "", termsplit[2])
    searchString <- gsub("%c%", city, bsearch) %>% gsub("%s%", state, .)
    apiResults <- searchString %>% GET #%>% prettify %>% fromJSON
    tryCatch({
        searchResult <- apiResults %>% prettify %>% fromJSON
        DFLocMatch <- rbind(DFLocMatch, data.frame(
            location=DFUniqueLocs$location[i], lat=searchResult$lat[1],
            lon=searchResult$lon[1])
        )
    }, error=function(e){
        cat("ERROR row ", i, ", ", term, ":", conditionMessage(e), "\n")})
}


write.csv(DFLocMatch, "~/Downloads/LocMathces.csv", row.names=FALSE)

DFLocCombined <- DFLocs %>% left_join(DFLocMatch) %>% na.omit
head(DFLocCombined)

write.csv(DFLocCombined, "~/Downloads/LocCombined.csv", row.names=FALSE)
