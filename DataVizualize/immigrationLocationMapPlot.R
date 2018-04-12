rm(list=ls())

library(leaflet)
library(dplyr)
library(ggplot2)
library(jsonlite)
library(cluster)
library(sp)
library(maps)
library(maptools)
library(RTextTools)
library(tm)
library(topicmodels)
library(tidyr)
library(tidytext)
library(LDAvis)

latlong2state <- function(pointsDF) {
    # Prepare SpatialPolygons object with one SpatialPolygon
    # per state (plus DC, minus HI & AK)
    states <- map('state', fill=TRUE, col="transparent", plot=FALSE)
    IDs <- sapply(strsplit(states$names, ":"), function(x) x[1])
    states_sp <- map2SpatialPolygons(states, IDs=IDs,
                                     proj4string=CRS("+proj=longlat +datum=WGS84"))
    
    # Convert pointsDF to a SpatialPoints object 
    pointsSP <- SpatialPoints(pointsDF, 
                              proj4string=CRS("+proj=longlat +datum=WGS84"))
    
    # Use 'over' to get _indices_ of the Polygons object containing each point 
    indices <- over(pointsSP, states_sp)
    
    # Return the state names of the Polygons object containing each point
    stateNames <- sapply(states_sp@polygons, function(x) x@ID)
    stateNames[indices]
}


DFGeo <- read.csv("~/Documents/OpenProgress/DataVizualize/LocMathces.csv",
                  stringsAsFactors=F)
TweetJSON <- fromJSON("~/Documents/OpenProgress/DataVizualize/immigrationTweets.json")


N_ <- 1:nrow(TweetJSON)
TweetJSONSub <- data.frame(
    text=TweetJSON$text[N_],
    retext=TweetJSON$retweeted_status$text[N_],
    location=tolower(TweetJSON$user$location[N_]),
    stringsAsFactors=F) %>% 
    left_join(DFGeo, by="location") %>%
    filter(!is.na(lat)) %>%
    mutate(state=latlong2state(data.frame(lon, lat))) %>%
    filter(!is.na(state)) %>%
    mutate_at(c("text", "retext"), as.character) %>%
    mutate(text=ifelse(!is.na(retext), retext, text))

kclust <- TweetJSONSub %>% select(lon, lat) %>% as.matrix %>% kmeans(50)

leaflet() %>%
    addTiles() %>%  # Add default OpenStreetMap map tiles
    addMarkers(lng=kclust$centers[,1], 
               lat=kclust$centers[,2], 
               popup=as.character(kclust$size))

source <- VectorSource(TweetJSONSub$text)
corpus <- Corpus(source) %>%
    tm_map(content_transformer(tolower)) %>%
    tm_map(removeNumbers) %>%
    tm_map(removePunctuation) %>%
    tm_map(removeWords, stopwords("english"))

mat <- DocumentTermMatrix(corpus)
#mat4 <- weightTfIdf(mat) %>% as.matrix

k <- 10
lda <- LDA(mat, k)
tweet_topics <- tidy(lda, matrix = "beta")

if(FALSE){
    dLength <- mat %>% as.matrix %>% rowSums
    tOccur <- mat %>% as.matrix %>% colSums
    createJSON(
        exp(lda@beta), lda@gamma, dLength, lda@terms, tOccur
    ) %>%
        serVis
}


tweet_topics %>%
    group_by(topic) %>%
    top_n(10, beta) %>%
    ungroup() %>%
    arrange(topic, -beta) %>%
    mutate(term = reorder(term, beta)) %>%
    ggplot(aes(term, beta, fill = factor(topic))) +
    geom_col(show.legend = FALSE) +
    facet_wrap(~ topic, scales = "free") +
    coord_flip()
    

coDF <- (lapply(1:k, function(i) 
    (lapply(setdiff(1:k, i), function(j){
        comp_ <- paste0("topic ", i, " / topic ", j)
        t1 <- paste0("topic", i)
        t2 <- paste0("topic", j)
        tweet_topics %>%
            filter(topic == i | topic == j) %>%
            mutate(topic = paste0("topic", topic)) %>%
            spread(topic, beta) %>%
            rename(topicA=!!t1, topicB=!!t2) %>%
            filter(topicA > .001 | topicB > .001) %>%
            mutate(compare=comp_) %>%
            mutate(log_ratio = log2(topicA / topicB)) %>%
            arrange(-log_ratio) %>%
            filter(row_number()<=10 | row_number()>=(n()-9))
})) %>% bind_rows)) %>% bind_rows

coDF %>% 
    filter(startsWith(compare, "topic 1 ")) %>%
    mutate(compare=as.character(compare)) %>%
    ggplot(aes(reorder(term, -log_ratio), log_ratio)) + 
    geom_col(show.legend = FALSE) + 
    coord_flip() + 
    facet_wrap(~compare, scales="free")



norm_eucl <- function(m)
    m/apply(m,1,function(x) sum(x^2)^.5)
mat_norm <- norm_eucl(mat4)

# kclust$centers[,1]

leaflet() %>%
    addTiles() %>%  # Add default OpenStreetMap map tiles
    addMarkers(lng=kclust$centers[,1], 
               lat=kclust$centers[,2])
m  # Print the map

