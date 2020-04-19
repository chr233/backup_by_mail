import psutil
import platform
import smtplib
from datetime import datetime
from time import sleep
from pathlib import Path, PurePath

from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from config import *


def size2str(size: float) -> str:
    '''将字节转换成合适的单位
    输入：
        字节数
    返回：
        形如 1.0KB 的格式
    '''
    def sos(integer, remainder, level):
        if integer >= 1024:
            remainder = integer % 1024
            integer //= 1024
            level += 1
            return sos(integer, remainder, level)
        else:
            return integer, remainder, level

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']
    integer, remainder, level = sos(size, 0, 0)
    if level+1 > len(units):
        level = -1
    return (f'{integer}.{str(remainder)[:2]}{units[level]}')


def now():
    return(datetime.now())


def datetime2str(date: datetime) -> str:
    '''格式化日期和时间'''
    return(date.strftime("%Y年%m月%d日 %H:%M:%S"))


def date2str(date: datetime) -> str:
    '''格式化日期'''
    return(date.strftime("%Y年%m月%d日"))


def time2str(date: datetime) -> str:
    '''格式化时间'''
    return(date.strftime("%H:%M:%S"))


def get_host_name() -> str:
    '''返回主机名，优先返回config里设置的主机名'''
    name = host_name if host_name else platform.uname().node
    return(name)


def send_email(subject: str, message: str, attact_list: list = []):
    '''发送邮件
    参数：
        邮件主题
        邮件正文
        邮件附件列表，列表中每个元素为(文件名,字节集)
    '''
    mailobj = MIMEMultipart()

    mailobj['From'] = Header(f"{email_from}<{email_sender}>", 'utf-8')
    mailobj['To'] = Header(f"{email_to}<{email_receiver}>", 'utf-8')
    mailobj['Subject'] = Header(subject, 'utf-8')
    mailobj.attach(MIMEText(message, 'plain', 'utf-8'))

    if attact_list:
        for name, content in attact_list:
            part = MIMEApplication(content)
            part.add_header('Content-Disposition', 'attachment', filename=name)
            mailobj.attach(part)

    with smtplib.SMTP_SSL(host=smtp_host, port=smtp_port) as smtpObj:
        smtpObj.connect(host=smtp_host, port=smtp_port)
        smtpObj.login(smtp_user, smtp_pass)
        smtpObj.sendmail(email_sender, email_receiver, mailobj.as_string())


def gen_sys_info() -> (str, list):
    '''生成简单的系统状态文本，会产生5秒延时
    返回：
        系统状态清单
        警告信息
    '''
    def graph_process(percent: int, length: int = 15):
        '''生成进度条，percent为进度[0-100]，length为长度'''
        percent_count = int(length*percent/100)
        return(f'{str(percent).rjust(4)}% [{"#"*percent_count}{"_"*(length-percent_count)}]')

    def check_status():
        '''判断数值是否异常'''
        warns = []
        if cpu_percent >= 95:
            warns.append('  CPU负载过高\n')
        if mem_percent >= 95:
            warns.append('  内存占用过高\n')
        for load in cpu_load:
            if load+0.3 >= cpu_trade:
                warns.append('  系统负载过高\n')
                break
        for usage in disk_percent:
            if usage >= 95:
                warns.append('  磁盘空间不足\n')
                break
        if warns:
            return(f'警告信息：\n{"".join(warns)}\n')
        else:
            return(False)

    uname = platform.uname()
    sys_hostname = uname.node
    sys_type = uname.system
    if sys_type == 'Linux':
        sys_version = ' '.join(platform.dist())
    else:
        sys_version = f'{uname.system} {uname.version}'

    time_boot = datetime.fromtimestamp(psutil.boot_time())
    time_curr = datetime.now()
    time_pass = time_curr - time_boot

    cpu_percent = psutil.cpu_percent()
    cpu_core = psutil.cpu_count(logical=False)
    cpu_trade = psutil.cpu_count(logical=True)
    cpu_load = psutil.getloadavg()

    mem = psutil.virtual_memory()
    mem_total = mem.total
    mem_used = mem.used
    mem_percent = mem.percent

    disk_info = []
    disk_percent = []
    for d in psutil.disk_partitions():
        if d.fstype:
            usage = psutil.disk_usage(d.mountpoint)
            d_total = usage.total
            d_used = usage.used
            d_percent = usage.percent
            disk_percent.append(d_percent)
            disk_info.append(
                f'磁盘{d.mountpoint.ljust(9)}: '
                f'{graph_process(d_percent)} '
                f'{size2str(d_used)}/{size2str(d_total)}\n')
        else:
            d_total = 0
            d_used = 0
            d_percent = 0
            disk_info.append(
                f'磁盘{d.mountpoint.ljust(9)}: {graph_process(0)} 不可用\n')

    net_old = psutil.net_io_counters()
    sleep(5)
    net = psutil.net_io_counters()
    net_send_s = (net.bytes_sent - net_old.bytes_sent)//5
    net_recv_s = (net.bytes_recv - net_old.bytes_recv)//5

    net_send = net.bytes_sent
    net_recv = net.bytes_recv

    user_info = []
    for i, user in enumerate(psutil.users(), 1):
        u_name = user.name
        u_host = user.host
        u_start = user.started
        user_info.append(f'  {i}. {u_name} [{u_host}] 自 '
                         f'{datetime2str(datetime.fromtimestamp(u_start))}\n')

    warns = check_status()

    msg = (f'{"系统状态".center(50,"=")}\n'
           f'{warns if warns else ""}'
           f'主机名称{" "*6}：{sys_hostname}\n'
           f'系统版本{" "*6}：{sys_version}\n'
           '\n'
           f'当前时间{" "*6}：{datetime2str(time_curr)}\n'
           f'运行时间{" "*6}：{time_pass.days}天{int(time_pass.seconds//3600)}时\n'
           f'平均负载{" "*6}：{cpu_load[0]} {cpu_load[1]} {cpu_load[2]}\n'
           '\n'
           f'CPU使用{" "*6}：{graph_process(cpu_percent)} '
           f'{cpu_core}C{cpu_trade}T\n'
           f'内存使用{" "*6}：{graph_process(mem_percent)} '
           f'{size2str(mem_used)}/{size2str(mem_total)}\n'
           f'{"".join(disk_info)}\n'
           f'当前流量{" "*6}：{size2str(net_send_s)}/S 发送 {size2str(net_recv_s)}/S 接收\n'
           f'累计流量{" "*6}：{size2str(net_send)} 发送 {size2str(net_recv)} 接收\n'
           '\n'
           f'登陆用户{" "*6}：\n{"".join(user_info) if user_info else "  无登录用户"}'
           )
    return (msg, warns)


def gen_file_info(file_info: list) -> str:
    '''根据文件列表生成文件清单
    参数：
        文件信息列表,通过group_file_by_size生成
    返回：
        文件信息清单
    '''
    info_list = []
    total = 0
    i = 0
    for i, (name, *_, piece, size) in enumerate(file_info, 1):
        total += size
        if piece:
            info_list.append(
                f'{f"{i}".rjust(2)}.[{f"{size2str(size)}".rjust(8)}] {name} 【分{piece}块】\n'
            )
        else:
            info_list.append(
                f'{f"{i}".rjust(2)}.[{f"{size2str(size)}".rjust(8)}] {name}\n'
            )

    msg = (f'{"附件清单".center(50,"=")}\n'
           f'{"".join(info_list)}'
           f'{f"总计[{i}]个文件，占用[{size2str(total)}]空间".center(50,"=")}\n'
           )
    return(msg)


def gen_pack_info(file_group: list) -> str:
    '''(文件名,索引,文件块数,起始字节,读取字节)'''
    info_list = []
    total = 0
    i = 0
    for i, (name, *_, size) in enumerate(file_group, 1):
        total += size
        info_list.append(
            f'{f"{i}".rjust(2)}.[{f"{size2str(size)}".rjust(8)}] {name}\n'
        )

    msg = (f'{"附件清单".center(50,"=")}\n'
           f'{"".join(info_list)}'
           f'{f"总计[{i}]个文件，占用【{size2str(total)}】空间".center(50,"=")}\n'
           )
    return(msg)


def pack_file(file_info, file_group) -> list:
    '''按照文件组读取文件，两个参数可以用group_file_by_size获取
    参数：
        文件信息列表
        文件组列表
    返回：
        文件内容列表[(文件名,文件二进制数据),]
    '''
    pack_list = []
    for name, index, piece, start, size in file_group:
        try:
            path = file_info[index][1]
            with open(path, 'rb') as f:
                f.seek(start)
                content = f.read(size)
            if piece:
                pack_list.append((f'{name}.[{piece}]', content))
            else:
                pack_list.append((name, content))

        except FileNotFoundError:
            print(f'**文件{name}不存在**')
        except IndexError:
            print('**索引越界，请检查传入列表是否对应**')
    return(pack_list)


def sort_file_list(dir_path: list) -> list:
    '''根据目录生成文件列表，并按照文件尺寸从大到小的顺序排序
    参数：
        目录路径
    返回：
        排过序的目录列表，每个元素为[(文件名,文件路径,文件尺寸),]
    '''
    try:
        files = []
        with Path(dir_path) as p:
            for x in p.iterdir():
                # 只处理文件
                if x.is_file():
                    file_path = str(PurePath(dir_path, x.name))
                    file_size = x.stat().st_size
                    files.append((file_path, x.name, file_size))
        files.sort(key=lambda x: x[2], reverse=True)
    except FileNotFoundError:
        print(f'**目录[{dir_path}]不存在**')
    return(files)


def group_file_by_size(file_list: list, max_size: int = 50331648, min_size: int = 1048576) -> (list, list):
    '''把文件切分、打包成合适的大小
    参数：
        有序文件列表(需要先按照文件尺寸排序(sort_file_list))
        文件组的最大大小(字节)
        文件切片的最小大小(字节)(防止出现非常小的切片)
    返回：
        文件信息列表,[(文件名,路径,总文件块数,总大小),]
        文件块列表,[(文件名,索引,文件块数,起始字节,读取字节),]
    '''
    file_info = []  # 记录文件名，路径，文件切片数(不切片为0)
    group_list = []  # 记录文件分组(文件名,起始,大小,尺寸)

    group = []  # 文件组变量
    used_size = 0  # 已用空间

    while len(file_list):
        # 三个状态：
        # 空的组，pop第一个文件，切分塞入
        # 组非空，找到最适合的文件塞入
        # 组非空，找不到适合的文件，关闭组，开启下一组。
        if used_size == 0:
            # 新的附件空间
            free_size = max_size

            # 取出一个文件
            file_path, file_name, file_size = file_list.pop(0)

            f_size = file_size

            piece = 0  # 文件块数数(0=不切割)
            start = 0  # 文件首字节
            size = 0  # 文件结束字节

            while file_size > 0:
                if file_size >= max_size:
                    # 文件剩余部分大于等于空闲空间
                    file_size -= max_size
                    size = max_size
                    piece += 1

                    used_size = 0

                    group_list.append(
                        #[(f'{file_name}.[{piece}]', start, size)]
                        [(file_name, len(file_info), piece, start, size)]
                    )

                    start += max_size
                else:
                    # 文件剩余部分小于空闲空间

                    size = file_size
                    if piece:
                        piece += 1

                    used_size = file_size

                    file_size = 0

                    # 开始一个文件组
                    group = [
                        #(f'{file_name}{f".[{piece}]" if piece else None}', start, size)
                        (file_name, len(file_info), piece, start, size)
                    ]
                    file_info.append((file_name, file_path, piece, f_size))

                    if not file_list:
                        # 已经是最后一个文件
                        group_list.append(group)

        else:
            # 已经有文件的空间
            free_size = max_size - used_size

            # smallest_size = file_list[-1][2]
            if file_list[-1][2] <= free_size:
                # 空闲空间足够大，无需切割

                # 寻找能放得下的最大的文件
                for i, f in enumerate(file_list, 0):
                    if f[2] <= free_size:
                        break

                file_path, file_name, file_size = file_list.pop(i)

                f_size = file_size

                start = 0
                size = file_size

                used_size += file_size

                group.append((file_name, len(file_info), 0, start, size))
                file_info.append((file_name, file_path, 0, f_size))

                if not file_list:
                    # 已经是最后一个文件
                    group_list.append(group)
            else:
                # 最小文件大小大于空闲空间
                if free_size > min_size:
                    # 无法放下任何文件,但是允许切分文件

                    file_path, file_name, file_size = file_list.pop(0)
                    f_size = file_size

                    file_size -= free_size
                    piece = 1
                    start = 0
                    size = free_size

                    # 切分第一部分
                    group.append(
                        #(f'{file_name}.[{piece}]', start, size)
                        (file_name, len(file_info), piece, start, size)
                    )
                    group_list.append(group)

                    start += size

                    used_size = 0
                    group = []

                    # 安排文件的后续部分
                    while file_size > 0:
                        if file_size >= max_size:
                            # 后续部分大于等于最大空间
                            file_size -= max_size

                            size = max_size
                            piece += 1

                            # 直接封装文件组
                            group_list.append(
                                #[(f'{file_name}.[{piece}]', start, size)]
                                [(file_name, len(file_info), piece, start, size)]
                            )

                            start += size

                        else:
                            # 后续部分小于最大空间
                            size = file_size
                            piece += 1

                            used_size = file_size

                            file_size = 0

                            # 开始一个文件组
                            group = [
                                #(f'{file_name}.[{piece}]', start, size)
                                (file_name, len(file_info), piece, start, size)
                            ]
                            file_info.append(
                                (file_name, file_path, piece, f_size))

                            if not file_list:
                                # 已经是最后一个文件
                                group_list.append(group)

                else:
                    # 无法放下任何文件，不允许切分文件，开始新组
                    group_list.append(group)
                    group = []
                    used_size = 0

    return((file_info, group_list))