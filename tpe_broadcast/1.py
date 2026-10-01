from pyproj import Transformer

# always_xy=True 會強制輸入為 (X, Y)，輸出為 (Lng, Lat)
transformer = Transformer.from_crs("epsg:3826", "epsg:4326", always_xy=True)

# 傳入 csX, csY
lng, lat = transformer.transform(301748.2369, 2770170.7969)

print(f"經緯度: {lat:.6f}, {lng:.6f}")
# 正確輸出約為：25.037126, 121.512371（臺北市中正區）