# coding = utf-8
"""
Step 3: MAFFT 多序列比对

【输入】
    - input_fasta: str, 去冗余后的 FASTA 文件
    - output_dir: str, 输出目录
    - config: PipelineConfig, 配置参数

【输出】
    - homologs.aln: str, Clustal 格式的比对结果
    - .step3_mafft_done: str, 断点标记文件

【原理】
    MAFFT 使用 FFT (Fast Fourier Transform) 加速比对，
    --localpair 对远距离同源序列效果更好，
    --maxiterate 1000 允许更多迭代以提高精度。
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


def run_mafft(
    input_fasta: str,
    output_dir: str,
    threads: int = 16,
    config: PipelineConfig = None,
) -> str:
    """
    运行 MAFFT 多序列比对

    Args:
        input_fasta: 输入 FASTA 文件
        output_dir: 输出目录
        threads: 线程数
        config: 配置对象

    Returns:
        比对结果 (Clustal) 文件路径
    """
    if config is None:
        config = default_config

    os.makedirs(output_dir, exist_ok=True)

    # 检查断点
    checkpoint_file = os.path.join(output_dir, ".step3_mafft_done")
    aln_file = os.path.join(output_dir, "homologs.aln")
    if os.path.exists(checkpoint_file) and os.path.exists(aln_file):
        logger.info(f"[STEP3] Resume: alignment already exists")
        return aln_file

    if not os.path.exists(input_fasta):
        raise FileNotFoundError(f"Input fasta not found: {input_fasta}")

    # MAFFT 命令
    mafft_options = config.get_mafft_cmd()
    cmd = (
        f"mafft {mafft_options} "
        f"--thread {threads} "
        f"--clustalout "
        f"{input_fasta} > {aln_file}"
    )

    logger.info(f"[STEP3] Running MAFFT ({config.mafft_strategy}, iter={config.mafft_iterations})...")
    logger.info(f"[STEP3] CMD: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"[STEP3] MAFFT failed: {result.stderr}")
        raise RuntimeError(f"MAFFT failed: {result.stderr}")

    if not os.path.exists(aln_file) or os.path.getsize(aln_file) == 0:
        logger.error(f"[STEP3] MAFFT produced empty output")
        raise RuntimeError(f"MAFFT produced empty output")

    logger.info(f"[STEP3] MAFFT completed: {aln_file}")

    # 创建断点标记
    Path(checkpoint_file).touch()

    return aln_file


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python step3_mafft.py <input_fasta> <output_dir> [threads]")
        sys.exit(1)

    input_fasta = sys.argv[1]
    output_dir = sys.argv[2]
    threads = int(sys.argv[3]) if len(sys.argv) > 3 else 16

    run_mafft(input_fasta, output_dir, threads)
