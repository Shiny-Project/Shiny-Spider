# Shiny-Spider

## 部署
Require Python 3.7+

```
git clone https://github.com/Shiny-Project/Mirai
cd ./Mirai
pip install -r requirements.txt
mv ./core/config.py.example ./core/config.py
# Edit config.py
python Main.py ignite
```

Or using docker

```
docker pull ghcr.io/shiny-project/shiny-spider:1.0
docker run -d --rm --name shiny-spider-node shiny-spider -e SHINY_API_KEY="" -e SHINY_API_SECRET_KEY="" -e SHINY_API_HOST=""
```