"""
CSV内容重构脚本。

遍历input目录下的CSV文件，根据pattern.yaml中的正则表达式匹配content列，
提取匹配的数据并添加Hash主键和abbreviation字段，保存到output目录。
"""

import yaml
import pandas as pd
import re
import hashlib
from pathlib import Path
from logging_config import setup_logger


def load_config(config_file):
    """加载YAML配置文件"""
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_hash(row):
    """根据行内容生成MD5 Hash作为主键"""
    # 使用 content, x, y, z, layer 组合生成唯一标识
    # 将所有字段转换为字符串，处理可能的 None/NaN
    content = str(row.get("content", ""))
    x = str(row.get("x", ""))
    y = str(row.get("y", ""))
    z = str(row.get("z", ""))
    layer = str(row.get("layer", ""))

    raw_str = f"{content}{x}{y}{z}{layer}"
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest()


def process_csv_file(input_file, output_file, patterns, logger):
    """处理单个CSV文件"""
    try:
        logger.info(f"正在读取文件: {input_file}")
        df = pd.read_csv(input_file)

        # style 列可能不存在，如果不存在则补全为 NaN
        if "style" not in df.columns:
            df["style"] = None

        # 检查 content 列是否存在
        if "content" not in df.columns:
            logger.warning(f"文件 {input_file} 缺少 content 列，跳过")
            return

        # 准备结果列表
        results = []

        # 遍历每一行
        for _, row in df.iterrows():
            content = row["content"]

            # 跳过空内容
            if pd.isna(content) or content == "":
                continue

            content_str = str(content).strip()

            # 尝试匹配所有定义的模式
            for _, pattern_config in patterns.items():
                regex = pattern_config.get("code")
                abbreviation = pattern_config.get("abbreviation")

                if not regex:
                    continue

                try:
                    # 1. 匹配 Code (Regex)
                    if regex and re.match(regex, content_str):
                        # 匹配成功，提取数据
                        # 1.1 添加原始匹配项 (Code)
                        item = {
                            "content": content_str,
                            "x": row.get("x"),
                            "y": row.get("y"),
                            "z": row.get("z"),
                            "layer": row.get("layer"),
                            "style": row.get("style"),
                        }
                        item["id"] = generate_hash(item)
                        results.append(item)

                        # 假设一个 content 只属于一种类型，匹配到一个就 break
                        break

                    # 2. 匹配 Abbreviation (Exact String)
                    elif abbreviation and content_str == abbreviation:
                        item = {
                            "content": content_str,
                            "x": row.get("x"),
                            "y": row.get("y"),
                            "z": row.get("z"),
                            "layer": row.get("layer"),
                            "style": row.get("style"),
                        }
                        item["id"] = generate_hash(item)
                        results.append(item)
                        break

                except re.error as e:
                    logger.error(f"正则表达式错误 {regex}: {e}")

        # 如果有匹配结果，保存到文件
        if results:
            result_df = pd.DataFrame(results)
            # 调整列顺序，ID放第一位
            cols = ["id", "content", "x", "y", "z", "layer", "style"]
            result_df = result_df[cols]

            result_df.to_csv(output_file, index=False, encoding="utf-8-sig")
            logger.info(
                f"已保存重构数据到: {output_file} (提取 {len(result_df)} 条记录)"
            )
        else:
            logger.info(f"文件 {input_file} 中未找到匹配的数据")

    except Exception as e:
        logger.error(f"处理文件 {input_file} 时出错: {str(e)}")


def main():
    # 加载配置
    config = load_config("config.yaml")
    pattern_config = load_config("pattern.yaml")

    # 设置日志
    logger = setup_logger(
        log_level=getattr(__import__("logging"), config["log_level"]),
        log_file="./logs/refactor_csv.log",
    )

    logger.info("=" * 60)
    logger.info("开始重构CSV文件内容")
    logger.info("=" * 60)

    patterns = pattern_config.get("pattern_mapping", {})
    if not patterns:
        logger.error("pattern.yaml 中未找到 pattern_mapping 配置")
        return

    logger.info(f"加载了 {len(patterns)} 个匹配模式")

    # 获取输入输出目录
    input_dir = Path(config["paths"]["input_dir"])
    output_dir = Path(config["paths"]["output_dir"])

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 清空输出目录下的CSV文件
    logger.info(f"正在清空输出目录: {output_dir}")
    for existing_file in output_dir.glob("*.csv"):
        try:
            existing_file.unlink()
            logger.debug(f"已删除文件: {existing_file.name}")
        except Exception as e:
            logger.error(f"删除文件 {existing_file.name} 失败: {e}")

    # 获取所有CSV文件
    csv_files = list(input_dir.glob("*.csv"))

    if not csv_files:
        logger.warning(f"在 {input_dir} 中未找到CSV文件")
        return

    # 处理每个CSV文件
    for csv_file in csv_files:
        output_file = output_dir / f"refactored_{csv_file.name}"
        process_csv_file(csv_file, output_file, patterns, logger)

    logger.info("=" * 60)
    logger.info("CSV重构完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
