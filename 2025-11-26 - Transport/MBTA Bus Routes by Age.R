library(sf)
library(ggplot2)
library(readxl)
library(dplyr)
library(maptiles)
library(ggspatial)

#read in routes

routes <- read_sf("MBTABUSROUTES_ARC.shp")
routes <- rename(routes, Route = MBTA_ROUTE)
routes <- st_transform(routes, crs = 3857)

#read in ages
ages <- read_excel("AGe of Bus routes.xlsx", sheet = 1)

#join data
routes_with_age <- left_join(routes, ages, by = "Route" )

routes_with_age_clean <- routes_with_age[!is.na(routes_with_age$`First Bus Date`),]
routes_with_age_clean <- routes_with_age_clean[order(routes_with_age_clean$`First Bus Date`),]

#get basemap
basemap <- get_tiles(routes_with_age_clean, provider = "Esri.WorldGrayCanvas", crop = TRUE)

# plot map
ggplot(data = routes_with_age_clean) +
  layer_spatial(basemap) +
  geom_sf(aes(color = `First Bus Date`), linewidth = 1.3) +
  scale_color_viridis_c(option = "inferno", 
                        guide = guide_colorbar(
                          barheight = unit(1, "npc"),
                          title.position="right",
                          title.theme = element_text(angle = 270, hjust = 0.5),
                          ),
                        name = "MBTA Bus Routes by Year of First Bus"
  ) +
  coord_sf(expand = FALSE) +
  theme_void()+

theme(
    plot.margin = margin(0, 0, 0, 0),
    panel.spacing = unit(0, "lines"),
    text = element_text(color = "#22211d"),
    plot.background = element_rect(fill = "#D0CFD4", color = NA),
    legend.text = element_text(family = "mono",
      size = 15, hjust = 0.5, color = "#4e4d47",
      #margin = margin(b = -0.1, t = 0.4, l = 2, unit = "cm")
    ),
    legend.title = element_text(family = "mono",
      size = 15, hjust = 0.5, color = "#4e4d47", face = "bold",
      margin = margin(r = 0.2, l = .7, unit = "cm")
    )
)
