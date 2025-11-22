# GetCsvInfo

CSV文件处理工具，用于从能耗计量系统平面图元素CSV文件中提取指定列。

## 功能特性

- 从input目录读取多个CSV文件
- 根据文件名关键词自动识别配置
- 提取指定的列并保存到output目录
- 使用日志记录处理过程
- 支持自定义列配置

## 项目结构

```text
GetCsvInfo/
├── config.yaml           # 公共配置文件（日志、路径等）
├── private.yaml          # 私有配置文件（列映射配置）
├── pattern.yaml          # 正则表达式配置文件
├── logging_config.py     # 日志配置模块
├── refactor_csv.py       # CSV重构主脚本（正则匹配与重构）
├── useless_process_csv.py # 旧版CSV处理脚本（仅列提取）
├── input/                # 输入CSV文件目录
│   ├── 01 B2能耗计量系统平面图_elements.csv
│   ├── 02 B1能耗计量系统平面图_elements.csv
│   └── ...
├── output/               # 输出CSV文件目录
│   ├── refactored_01 B2能耗计量系统平面图_elements.csv
│   └── ...
└── logs/                 # 日志文件目录
    ├── refactor_csv.log
    └── process_csv.log
```


## 配置说明

### private.yaml - 列映射配置

在`private.yaml`中定义文件名关键词与需要提取的列的映射关系：

```yaml
csv_columns_mapping:
  B2:  # 文件名包含B2的文件
    columns:
      - type
      - color
      - content
      - layer
      - x
      - y
      - z
    description: "B2能耗计量系统平面图元素"
  
  L1:  # 文件名包含L1的文件（包括L1M1, L1M2）
    columns:
      - type
      - color
      - content
      - layer
      - x
      - y
      - z
    description: "L1能耗计量系统平面图元素"
```

支持的关键词：

- `B2` - B2层级文件
- `B1` - B1层级文件
- `L1` - L1层级文件（包括L1M1、L1M2）
- `L2` - L2层级文件（包括L2M）
- `L3` - L3层级文件（包括L3M1、L3M2）
- `default` - 默认配置

### config.yaml - 公共配置

```yaml
# 日志配置
log_level: INFO
log_file: ./logs/app.log

# 输入/输出配置
paths:
  input_dir: ./input
  output_dir: ./output
```

### pattern.yaml - 编码识别配置

用于识别CSV内容中的设备编码格式。

#### 1. 能耗计量 (Heat_Meter)

- **描述**: 能耗计量
- **缩写**: `NB`
- **编码规则**: 完整匹配8位数字，对应时代领宇的能耗计量编号
- **示例**: `00222227`
- **正则**: `^\d{8}$`

#### 2. 水表计量 (Water_Meter)

- **描述**: 水表计量
- **缩写**: `SB`
- **编码规则**: 完整匹配水表上编码 (JY + 9位数字)
- **示例**: `JY240311537`
- **正则**: `^JY\d{9}$`

#### 3. 弱电设计系统编号 (弱电设计)

- **描述**: 弱电设计系统编号
- **缩写**: (无)
- **编码规则**: 部分匹配弱电系统编号 (楼层-竖井-暖表|水表-编号)
- **示例**: `L3M1-E8-3-NB-01-01`
- **正则**: `^(B1|B2|L1|L1M1|L1M2|L2|L2M|L3|L3M1|L3M2)-[A-Z]\d-\d-`
  - 示例: `00222227`
  - 正则: `^\d{8}$`

#### 2. 水量 (Water Meter)

- **关键词**: `水量`
- **缩写**: `SB`
- **弱电系统编号 (ELV_drawing_code)**:
  - 规则: `楼层-竖井-暖表|水表-编号`
  - 正则: `^(B1|B2|L1|L1M1|L1M2|L2|L2M|L3|L3M1|L3M2)-[A-Z]\d-\d-`
- **完整编号 (Water_Meter_full_code)**:
  - 规则: JY + 9位数字
  - 示例: `JY240311537`
  - 正则: `^JY\d{9}$`

## 使用方法

1. 将CSV文件放入`input/`目录
2. 在`private.yaml`中配置需要提取的列
3. 运行处理脚本：

```bash
python process_csv.py
```

处理后的文件将保存在`output/`目录，文件名前缀为`filtered_`

## 输出示例

原始CSV文件有23列：

```text
type, center_x, center_y, center_z, color, content, end_x, end_y, end_z, 
height, layer, linetype, lineweight, radius, rotation, start_x, start_y, 
start_z, style, width, x, y, z
```

处理后的CSV文件只包含配置的7列：

```text
type, color, content, layer, x, y, z
```

## 日志

处理过程中的日志会输出到：

- 控制台（实时显示）
- 文件：`logs/app.log`

日志示例：

```text
2025-11-19 10:52:59,320 - INFO - process_csv - 处理文件: 01 B2能耗计量系统平面图_elements.csv (关键词: B2)
2025-11-19 10:52:59,347 - INFO - process_csv - 已保存到: output\filtered_01 B2能耗计量系统平面图_elements.csv (保留 7 列, 2467 行)
```

## 依赖包

- Python 3.x
- pandas
- PyYAML

## 注意事项

- 确保CSV文件使用UTF-8编码
- 如果配置的列在CSV文件中不存在，会在日志中显示警告
- 输出文件使用UTF-8 BOM编码，便于Excel打开
