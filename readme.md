# Shiny-Spider

## 部署
Using docker

```
docker pull ghcr.io/shiny-project/shiny-spider
docker run -d --rm --name shiny-spider-node shiny-spider -e SHINY_API_KEY="" -e SHINY_API_SECRET_KEY="" -e SHINY_API_HOST=""
```