# coding = utf-8
"""
Step 2: cd-hit 序列去冗余

【输入】
    - input_fasta: str, 同源基因 FASTA 文件路径
    - output_dir: str, 输出目录
    - config: PipelineConfig, 配置参数

【输出】
    - {prefix}_homologs.cdhit.fasta: str, 去冗余后的序列
    - .step2_cdhit_done: str, 断点标记文件

【原理】
    cd-hit 通过贪心算法将相似性 >= 阈值的序列聚类，
    每个 cluster 保留最长的序列作为代表序列。
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


def run_cdhit(
    input_fasta: str,
    output_dir: str,
    threads: int = 16,
    config: PipelineConfig = None,
) -> str:
    """
    运行 cd-hit 去冗余

    Args:
        input_fasta: 输入 FASTA 文件
        output_dir: 输出目录
        threads: 线程数
        config: 配置对象

    Returns:
        去冗余后的 FASTA 文件路径
    """
    if config is None:
        config = default_config

    os.makedirs(output_dir, exist_ok=True)

    # 检查断点
    checkpoint_file = os.path.join(output_dir, ".step2_cdhit_done")
    cdhit_fasta = os.path.join(output_dir, "homologs.cdhit.fasta")
    if os.path.exists(checkpoint_file) and os.path.exists(cdhit_fasta):
        logger.info(f"[STEP2] Resume: cdhit.fasta already exists")
        return cdhit_fasta

    if not os.path.exists(input_fasta):
        raise FileNotFoundError(f"Input fasta not found: {input_fasta}")

    # cd-hit 命令
    # -c: 相似性阈值, -n: word size (5 for 0.8 threshold), -T: threads, -M: memory (GB)
    cmd = (
        f"cd-hit "
        f"-i {input_fasta} "
        f"-o {cdhit_fasta} "
        f"-c {config.cdhit_identity} "
        f"-n 5 "
        f"-T {threads} "
        f"-M 8000"
    )

    logger.info(f"[STEP2] Running cd-hit (identity={config.cdhit_identity})...")
    logger.info(f"[STEP2] CMD: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"[STEP2] cd-hit failed: {result.stderr}")
        raise RuntimeError(f"cd-hit failed: {result.stderr}")

    logger.info(f"[STEP2] cd-hit completed: {cdhit_fasta}")

    # 统计去冗余结果
    try:
        with open(cdhit_fasta, "r") as f:
            seq_count = sum(1 for line in f if line.startswith(">"))
        logger.info(f"[STEP2] Sequences after cd-hit: {seq_count}")
    except:
        pass

    # 创建断点标记
    Path(checkpoint_file).touch()

    return cdhit_fasta


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python step2_cdhit.py <input_fasta> <output_dir> [threads]")
        sys.exit(1)

    input_fasta = sys.argv[1]
    output_dir = sys.argv[2]
    threads = int(sys.argv[3]) if len(sys.argv) > 3 else 16

    run_cdhit(input_fasta, output_dir, threads)
