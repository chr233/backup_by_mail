## 简介
本工具可以通过邮件附件备份本地文件，附带有发送系统状态报表的功能。
通过邮件备份文件，附带有发送系统状态报表的功能

## 配置
- 下载源码
- 安装前置库
 `pip3 install -r ./requirements.txt`
 或者
 `pip3 install psutil`
- 把`config.py.example`修改成`config.py`
 并按照里面的说明，设置SMTP账号信息。

## 使用示例
### 生成系统报告
`./run.py`

### 备份文件
`./run.py 要备份的目录`
> 一次只能处理第一个目录
> 使用QQ邮箱的话总大小最好控制在300MB以内，不然可能会收不到
> 如果使用其他邮箱，可能需要修改最大附件包大小，

### 被切分的文件还原
将A和B拼成C
- Windows
`copy /b A + B C`
- Linux
`cat A B > C`

备份文件总大小不要超过300MB，超出可能会被邮箱系统限流