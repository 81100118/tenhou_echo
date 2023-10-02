本仓库提供两种测试天凤连接质量的方法

建议至少连续运行数小时，若结果不可接受，建议使用游戏加速器打牌（并确保加速器对天凤生效）。加速器对此脚本似乎不能生效

免责声明：运行脚本的风险自负，使用/不使用游戏加速器由你自己决定，风险自负

# tenhou_echo.py: 模拟客户端登录NoName运行天凤4K版自带的echo

需要python3环境

和实际打牌情况较为接近

运行方式：`python tenhou_echo.py`

若要使用代理，需要在运行脚本前`export https_proxy="host:port"` host:port替换为代理服务器地址和端口

每秒向天凤服务器发送echo消息一次，会持续运行直到掉线

按Ctrl+C手动终止

输出样例：

`recv: 580 , timeout: 26 , avg echo: 157 ms, over 400ms count: 6 , over 1000ms count: 9`

按时收到580次，超时26次（超时时间为5秒），平均往返时延157ms，400ms-1000ms 6次，超过1000ms9次

推荐解读方法：timeout一次即不可接受

# ping_tenhou.bat: ping 天凤服务器并记录超时情况

需要windows系统

运行方式：双击或在cmd中运行

每秒ping一次天凤服务器（无法使用代理），正常情况下什么都不会输出，若超时，会输出相应信息至控制台和文件`pingNG.txt`

输出样例：

```
Ping NG 10/02/2023 Mon 20:18:21.15 143 
Ping NG 10/02/2023 Mon 20:18:26.18 144 
Ping NG 10/02/2023 Mon 20:18:31.18 145 
Ping NG 10/02/2023 Mon 20:18:36.19 146 
Ping NG 10/02/2023 Mon 20:18:41.17 147 
Ping NG 10/02/2023 Mon 20:18:46.20 148 
Ping NG 10/02/2023 Mon 20:20:08.21 226 
```

格式为日期 时间 ping序号

推荐解读方法：偶尔超时可以接受，需要特别注意突发的连续数次超时（例如样例中143-148），此时打牌基本会掉线，不可接受

