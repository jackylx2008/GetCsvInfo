"""
CSV文件处理脚本。

从input目录读取CSV文件，根据private.yaml中的配置提取指定列，
并将处理后的数据保存到output目录。
"""

import yaml
import pandas as pd
from pathlib import Path
from logging_config import setup_logger


def load_config(config_file):
    """
    加载YAML配置文件。

    :param config_file: 配置文件路径
    :return: 配置字典
    """
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_file_keyword(filename):
    """
    从文件名中提取关键词。

    :param filename: 文件名
    :return: 关键词（B2能耗计量, B1能耗计量, L1M2能耗计量等）
    """
    # 移除文件扩展名
    name = Path(filename).stem

    # 按优先级匹配关键词（从最具体到最一般）
    keywords = [
        "L3M2能耗计量",
        "L3M1能耗计量",
        "L2M能耗计量",
        "L1M2能耗计量",
        "L1M1能耗计量",
        "B2能耗计量",
        "B1能耗计量",
        "L3能耗计量",
        "L2能耗计量",
        "L1能耗计量",
    ]

    for keyword in keywords:
        if keyword in name:
            return keyword

    return "default"


def process_csv_file(input_file, output_file, columns, logger):
    """
    处理单个CSV文件，提取指定列并保存。

    :param input_file: 输入CSV文件路径
    :param output_file: 输出CSV文件路径
    :param columns: 需要提取的列列表
    :param logger: 日志记录器
    """
    try:
        # 读取CSV文件
        logger.info(f"正在读取文件: {input_file}")
        df = pd.read_csv(input_file)

        # 检查列是否存在
        available_columns = df.columns.tolist()
        missing_columns = [col for col in columns if col not in available_columns]

        if missing_columns:
            logger.warning(f"文件 {input_file} 中缺少以下列: {missing_columns}")

        # 提取存在的列
        existing_columns = [col for col in columns if col in available_columns]

        if not existing_columns:
            logger.error(f"文件 {input_file} 中没有任何指定的列")
            return

        # 提取数据
        df_filtered = df[existing_columns]

        # 保存到输出文件
        df_filtered.to_csv(output_file, index=False, encoding="utf-8-sig")
        logger.info(
            f"已保存到: {output_file} "
            f"(保留 {len(existing_columns)} 列, {len(df_filtered)} 行)"
        )

    except Exception as e:
        logger.error(f"处理文件 {input_file} 时出错: {str(e)}")


def main():
    """
    主函数。
    """
    # 加载公共配置
    config = load_config("config.yaml")

    # 设置日志
    logger = setup_logger(
        log_level=getattr(__import__("logging"), config["log_level"]),
        log_file="./logs/process_csv.log",
    )

    logger.info("=" * 60)
    logger.info("开始处理CSV文件")
    logger.info("=" * 60)

    # 加载私有配置
    try:
        private_config = load_config("private.yaml")
        csv_mapping = private_config.get("csv_columns_mapping", {})
        logger.info(f"已加载列映射配置，包含 {len(csv_mapping)} 个关键词")
    except Exception as e:
        logger.error(f"无法加载private.yaml: {str(e)}")
        return

    # 获取输入输出目录
    input_dir = Path(config["paths"]["input_dir"])
    output_dir = Path(config["paths"]["output_dir"])

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取所有CSV文件
    csv_files = list(input_dir.glob("*.csv"))

    if not csv_files:
        logger.warning(f"在 {input_dir} 中未找到CSV文件")
        return

    logger.info(f"找到 {len(csv_files)} 个CSV文件")

    # 处理每个CSV文件
    for csv_file in csv_files:
        # 提取文件关键词
        keyword = get_file_keyword(csv_file.name)
        logger.info(f"\n处理文件: {csv_file.name} (关键词: {keyword})")

        # 获取对应的列配置
        if keyword in csv_mapping:
            columns = csv_mapping[keyword]["columns"]
            description = csv_mapping[keyword].get("description", "")
            logger.info(f"配置说明: {description}")
        else:
            logger.warning(f"未找到关键词 '{keyword}' 的配置，使用默认配置")
            columns = csv_mapping.get("default", {}).get("columns", [])

        if not columns:
            logger.warning(f"没有为 {csv_file.name} 指定要提取的列，跳过")
            continue

        logger.info(f"将提取以下列: {', '.join(columns)}")

        # 生成输出文件名
        output_file = output_dir / f"filtered_{csv_file.name}"

        # 处理文件
        process_csv_file(csv_file, output_file, columns, logger)

    logger.info("=" * 60)
    logger.info("CSV文件处理完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
