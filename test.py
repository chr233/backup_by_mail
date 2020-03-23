from core import *
from run import *

# 虚拟文件列表
dic1 = [('100M', '100M', 1024*1024*100), ('90M', '90M', 1024*1024*90),
        ('89M', '89M', 1024*1024*89), ('77M', '77M', 1024*1024*77),
        ('69M', '69M', 1024*1024*69), ('51M', '51M', 1024*1024*51),
        ('46M', '46M', 1024*1024*46), ('32M', '32M', 1024*1024*32),
        ('38M', '38M', 1024*1024*38), ('20M', '20M', 1024*1024*20),
        ('10M', '10M', 1024*1024*10), ('1M', '1M', 1024*1024),
        ('40K', '40K', 1024*40), ('10K', '10K', 1024*10),
        ('3K', '3K', 1024*3), ('1K', '1K', 1024*1)]

# 真实文件列表
dic2 = sort_file_list(r'.')


# 文件分组测试
file_info, group_list = group_file_by_size(dic2, 1024*1024*50, 1024*1024)

print('='*50)
total_piece = 0
for name, path, piece, total_size in file_info:
    total_piece += piece
print(f'总文件块数 {total_piece}')
print(f'总包数 {len(group_list)}')
for group in group_list:
    pack_file(file_info, group)
    total_size = 0
    names = []
    for name, *_, start, size in group:
        total_size += size
        names.append(f'{name} {size2str(size)}')
        #print(f'  {n}({size2str(size)})')
    print(names)
    print(f'总尺寸 {total_size}({size2str(total_size)})')

# 生成系统报表
# print(gen_sys_info())
mail_backup('.')