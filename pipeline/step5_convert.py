# coding = utf-8
"""
Step 5: Bio.AlignIO 格式转换 (Clustal -> FASTA)

【输入】
    - input_trimal_aln: str, trimAl 输出的 Clustal 文件
    - output_dir: str, 输出目录

【输出】
    - homologs.trimal.fasta: str, FastTree 可读的 FASTA 格式
    - .step5_convert_done: str, 断点标记
"""

import os
import sys
import logging
from pathlib import Path
from Bio import AlignIO

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_convert(input_trimal_aln: str, output_dir: str) -> str:
    """
    转换 Clustal 比对格式为 FASTA

    Args:
        input_trimal_aln: trimAl 输出 (Clustal)
        output_dir: 输出目录

    Returns:
        FASTA 格式文件路径
    """
    os.makedirs(output_dir, exist_ok=True)

    # 检查断点
    checkpoint_file = os.path.join(output_dir, ".step5_convert_done")
    trimal_fasta = os.path.join(output_dir, "homologs.trimal.fasta")
    if os.path.exists(checkpoint_file) and os.path.exists(trimal_fasta):
        logger.info("[STEP5] Resume: converted fasta already exists")
        return trimal_fasta

    if not os.path.exists(input_trimal_aln):
        raise FileNotFoundError(f"Input alignment not found: {input_trimal_aln}")

    logger.info("[STEP5] Converting clustal -> fasta...")

    try:
        alignment = AlignIO.read(input_trimal_aln, "clustal")
        AlignIO.write(alignment, trimal_fasta, "fasta")
        logger.info(f"[STEP5] Converted {len(alignment)} sequences to FASTA")
    except Exception as e:
        logger.error(f"[STEP5] Conversion failed: {e}")
        raise

    # 创建断点标记
    Path(checkpoint_file).touch()
    logger.info(f"[STEP5] Done: {trimal_fasta}")
    return trimal_fasta


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python step5_convert.py <input_trimal_aln> <output_dir>")
        sys.exit(1)

    run_convert(sys.argv[1], sys.argv[2])
