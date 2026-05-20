# coding = utf-8
"""
Step 4: trimAl 序列比对修剪

【输入】
    - input_aln: str, MAFFT 输出 (Clustal 格式)
    - output_dir: str, 输出目录
    - config: PipelineConfig, 配置参数

【输出】
    - homologs.trimal.aln: str, 修剪后的比对文件
    - .step4_trimal_done: str, 断点标记
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import PipelineConfig, default_config

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_trimal(
    input_aln: str,
    output_dir: str,
    config: PipelineConfig = None,
) -> str:
    """
    运行 trimAl 修剪

    Args:
        input_aln: 输入比对文件 (Clustal)
        output_dir: 输出目录
        config: 配置对象

    Returns:
        修剪后的比对文件路径
    """
    if config is None:
        config = default_config

    os.makedirs(output_dir, exist_ok=True)

    # 检查断点
    checkpoint_file = os.path.join(output_dir, ".step4_trimal_done")
    trimal_aln = os.path.join(output_dir, "homologs.trimal.aln")
    if os.path.exists(checkpoint_file) and os.path.exists(trimal_aln):
        logger.info("[STEP4] Resume: trimmed alignment already exists")
        return trimal_aln

    if not os.path.exists(input_aln):
        raise FileNotFoundError(f"Input alignment not found: {input_aln}")

    cmd = f"trimal -in {input_aln} -out {trimal_aln} -{config.trimal_strategy}"

    logger.info(f"[STEP4] Running trimAl ({config.trimal_strategy})...")
    logger.info(f"[STEP4] CMD: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"[STEP4] trimAl failed: {result.stderr}")
        raise RuntimeError(f"trimAl failed: {result.stderr}")

    if not os.path.exists(trimal_aln):
        raise RuntimeError("trimAl produced no output")

    # 创建断点标记
    Path(checkpoint_file).touch()
    logger.info(f"[STEP4] Done: {trimal_aln}")
    return trimal_aln


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python step4_trimal.py <input_aln> <output_dir>")
        sys.exit(1)

    run_trimal(sys.argv[1], sys.argv[2])
