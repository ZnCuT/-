# 四史语料库新结构使用指南

## 新的目录结构

```
data/
  raw/
    shiji/           # 史记
      benji/         # 本纪
        01_五帝本纪.txt
        02_夏本纪.txt
      shijia/        # 世家  
        01_吴太伯世家.txt
        02_齐太公世家.txt
      liezhuan/      # 列传
        01_伯夷列传.txt
        02_管晏列传.txt
      shu/           # 书
        01_河渠书.txt
        02_平准书.txt
      biao/          # 表
        01_三代世表.txt
        02_十二诸侯年表.txt
    hanshu/          # 汉书
      benji/         # 本纪（12篇）
      biao/          # 表（8篇）
      zhi/           # 志（10篇）
      liezhuan/      # 列传（70篇）
    houhanshu/       # 后汉书
      leibian/       # 类传（7篇）
    sanguozhi/       # 三国志
      wei/           # 魏书
      shu/           # 蜀书
      wu/            # 吴书
```

## 文件格式

每个txt文件包含一个章节的三平行语料，格式如下：

```
文言文段落1
白话文段落1  
英文段落1

文言文段落2
白话文段落2
英文段落2

...
```

## 数据迁移

### 1. 从旧格式迁移到新格式

```bash
python migrate_data.py
```

这会将现有的大文件格式（wenyan.txt, zh.txt, en.txt）转换为新的分类目录结构。

### 2. 备份和切换

```bash
# 备份原数据
mv data/raw data/raw_backup

# 使用新数据
mv data/raw_new data/raw
```

## 添加新语料的方法

### 方法1: CSV批量导入（推荐）

1. 创建CSV模板：
```bash
python batch_import.py template
```

2. 编辑template.csv，添加您的数据：
```csv
book,category,chapter_num,title,wenyan,zh,en
shiji,benji,1,五帝本纪,昔在黄帝...,从前黄帝...,Long ago...
```

3. 导入数据：
```bash
python batch_import.py csv template.csv
```

### 方法2: Excel批量导入

1. 准备Excel文件，列名：book,category,chapter_num,title,wenyan,zh,en
2. 导入：
```bash
python batch_import.py excel your_data.xlsx
```

### 方法3: 单个txt文件导入

```bash
python batch_import.py txt chapter.txt shiji liezhuan 伯夷列传
```

### 方法4: 手动添加

直接在对应目录下创建txt文件：
```
data/raw/shiji/liezhuan/03_新章节.txt
```

## 验证数据

```bash
python batch_import.py validate
```

这会显示当前语料库的统计信息。

## 网站导航结构

新的网站导航路径：
- 首页 `/`
- 书籍列表 `/book/shiji/`（显示分类）
- 分类章节 `/book/shiji/liezhuan/`（显示章节列表）
- 具体章节 `/book/shiji/liezhuan/chapter/1/`（显示三平行内容）

## 支持的书籍和分类

### 史记 (shiji)
- benji: 本纪
- shijia: 世家
- liezhuan: 列传
- shu: 书
- biao: 表

### 汉书 (hanshu)
- benji: 本纪
- biao: 表
- zhi: 志
- liezhuan: 列传

### 后汉书 (houhanshu)
- leibian: 类传

### 三国志 (sanguozhi)
- wei: 魏书
- shu: 蜀书
- wu: 吴书

## 注意事项

1. **文件名规范**：建议使用 `序号_标题.txt` 格式，如 `01_五帝本纪.txt`
2. **编码**：所有文件使用UTF-8编码
3. **备份**：添加新语料前建议备份现有数据
4. **验证**：导入后运行验证命令检查数据完整性

## 后续扩展

如需添加新的书籍或分类，可以：
1. 在 `batch_import.py` 中的 `BOOK_CATEGORIES` 添加配置
2. 在 `app.py` 中更新对应配置
3. 确保目录结构和导航逻辑的一致性