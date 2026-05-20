# coding = utf-8
"""
Step 6: FastTree 进化树构建

【输入】
    - input_fasta: str, 比对后的 FASTA 文件
    - output_dir: str, 输出目录
    - threads: int, 线程数
    - config: PipelineConfig, 配置参数

【输出】
    - result.treefile: str, Newick 格式进化树
    - .step6_fasttree_done: str, 断点标记
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


def run_fasttree(
    input_fasta: str,
    output_dir: str,
    threads: int = 4,
    config: PipelineConfig = None,
) -> str:
    """
    运行 FastTree 建树

    Args:
        input_fasta: 输入 FASTA 文件
        output_dir: 输出目录
        threads: 线程数
        config: 配置对象

    Returns:
        Newick 树文件路径
    """
    if config is None:
        config = default_config

    os.makedirs(output_dir, exist_ok=True)

    # 检查断点
    checkpoint_file = os.path.join(output_dir, ".step6_fasttree_done")
    tree_file = os.path.join(output_dir, "result.treefile")
    if os.path.exists(checkpoint_file) and os.path.exists(tree_file):
        logger.info("[STEP6] Resume: treefile already exists")
        return tree_file

    if not os.path.exists(input_fasta):
        raise FileNotFoundError(f"Input fasta not found: {input_fasta}")

    cmd = (
        f"FastTree "
        f"-{config.fasttree_model} "
        f"-gamma "
        f"-boot {config.bootstrap} "
        f"-seed {config.fasttree_seed} "
        f"-threads {threads} "
        f"-log {os.path.join(output_dir, 'fasttree.log')} "
        f"{input_fasta} > {tree_file}"
    )

    logger.info(f"[STEP6] Running FastTree (model={config.fasttree_model}, boot={config.bootstrap})...")
    logger.info(f"[STEP6] CMD: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"[STEP6] FastTree failed: {result.stderr}")
        raise RuntimeError(f"FastTree failed: {result.stderr}")

    if not os.path.exists(tree_file):
        raise RuntimeError("FastTree produced no output")

    # 读取树文件确认内容
    with open(tree_file, "r") as f:
        tree_content = f.read().strip()
    node_count = tree_content.count(",") + 1
    logger.info(f"[STEP6] Tree built: {node_count} leaves")

    # 创建断点标记
    Path(checkpoint_file).touch()
    logger.info(f"[STEP6] Done: {tree_file}")
    return tree_file


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python step6_fasttree.py <input_fasta> <output_dir> [threads]")
        sys.exit(1)

    input_fasta = sys.argv[1]
    output_dir = sys.argv[2]
    threads = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    run_fasttree(input_fasta, output_dir, threads)
