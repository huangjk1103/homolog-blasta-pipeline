#!/usr/bin/env python3
# coding = utf-8
"""
命令行入口：运行 Pipeline

【用法】
    python run_pipeline.py \\
        --query /path/to/query.fasta \\
        --database /path/to/database/ \\
        --output /path/to/output/ \\
        --threads 32

【输入参数】
    --query        查询序列 FASTA 文件（必填）
    --database     BLAST 数据库目录（必填）
    --output       输出目录（必填）
    --threads      并行线程数（默认 16）
    --coverage     coverage 阈值，默认 0.7
    --evalue       E-value 阈值，默认 1e-5
    --cdhit        cd-hit 相似性阈值，默认 0.8
    --mafft-iterations  MAFFT 最大迭代次数，默认 1000
    --bootstrap    FastTree bootstrap 次数，默认 100
    --prefix       输出文件前缀，默认 homolog_analysis

【输出】
    进化树 (.treefile)、注释 (.xlsx)、统计 (.xlsx)
"""

import sys
import os
from pathlib import Path

# 添加 pipeline 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

from config import PipelineConfig
from pipeline import Pipeline


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Planctomycetota 同源基因分析 Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_pipeline.py \\
      --query /mnt/d/linux/1296_genome/homolog_blastp/T1NAG_00113.fasta \\
      --database /mnt/d/linux/1296_genome/1296_fna/database/ \\
      --output /mnt/d/linux/1296_genome/homolog_blastp/T1NAG_00113/ \\
      --threads 32 \\
      --coverage 0.7 \\
      --evalue 1e-5 \\
      --cdhit 0.8
        """,
    )

    parser.add_argument("--query", required=True, help="查询序列 FASTA 文件")
    parser.add_argument("--database", required=True, help="BLAST 数据库目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--threads", type=int, default=16, help="并行线程数（默认 16）")
    parser.add_argument("--coverage", type=float, default=0.7, help="coverage 阈值（默认 0.7）")
    parser.add_argument("--evalue", type=float, default=1e-5, help="E-value 阈值（默认 1e-5）")
    parser.add_argument(
        "--cdhit", type=float, default=0.8, help="cd-hit 相似性阈值（默认 0.8）"
    )
    parser.add_argument(
        "--mafft-iterations", type=int, default=1000, help="MAFFT 最大迭代次数（默认 1000）"
    )
    parser.add_argument("--bootstrap", type=int, default=100, help="FastTree bootstrap（默认 100）")
    parser.add_argument("--prefix", default="homolog_analysis", help="输出文件前缀")

    args = parser.parse_args()

    # 验证输入
    if not os.path.exists(args.query):
        print(f"错误: 查询文件不存在: {args.query}")
        sys.exit(1)
    if not os.path.isdir(args.database):
        print(f"错误: 数据库目录不存在: {args.database}")
        sys.exit(1)

    # 构建配置
    config = PipelineConfig(
        coverage=args.coverage,
        evalue=args.evalue,
        cdhit_identity=args.cdhit,
        mafft_iterations=args.mafft_iterations,
        bootstrap=args.bootstrap,
        output_prefix=args.prefix,
    )

    # 运行 Pipeline
    pipeline = Pipeline(
        query_fasta=args.query,
        database_dir=args.database,
        output_dir=args.output,
        threads=args.threads,
        config=config,
    )

    pipeline.run()


if __name__ == "__main__":
    main()
