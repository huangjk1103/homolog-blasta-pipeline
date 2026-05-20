# coding = utf-8
"""
Pipeline 主流程编排器

【功能】
    串联 step1~step8，自动检测断点续传

【输入】
    - query_fasta: 查询序列
    - database_dir: BLAST 数据库目录
    - output_dir: 输出目录
    - threads: 线程数
    - config: PipelineConfig

【输出】
    - 进化树文件 + 注释文件 + 统计文件
"""

import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import PipelineConfig, default_config

# 导入各步骤模块
from step1_blastp import run_blastp
from step2_cdhit import run_cdhit
from step3_mafft import run_mafft
from step4_trimal import run_trimal
from step5_convert import run_convert
from step6_fasttree import run_fasttree
from step7_annotation import run_annotation
from step8_stats import run_stats

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class Pipeline:
    """同源基因分析 Pipeline"""

    def __init__(
        self,
        query_fasta: str,
        database_dir: str,
        output_dir: str,
        threads: int = 16,
        config: PipelineConfig = None,
    ):
        self.query_fasta = query_fasta
        self.database_dir = database_dir
        self.output_dir = output_dir
        self.threads = threads
        self.config = config or default_config
        os.makedirs(self.output_dir, exist_ok=True)

        # 中间文件路径
        self.homologs_fasta = os.path.join(self.output_dir, "homologs.fasta")
        self.cdhit_fasta = os.path.join(self.output_dir, "homologs.cdhit.fasta")
        self.aln_file = os.path.join(self.output_dir, "homologs.aln")
        self.trimal_aln = os.path.join(self.output_dir, "homologs.trimal.aln")
        self.trimal_fasta = os.path.join(self.output_dir, "homologs.trimal.fasta")
        self.tree_file = os.path.join(self.output_dir, "result.treefile")

    def run(self):
        """执行完整 Pipeline"""
        logger.info("=" * 60)
        logger.info("Planctomycetota 同源基因分析 Pipeline 开始")
        logger.info(f"Query: {self.query_fasta}")
        logger.info(f"Database: {self.database_dir}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Threads: {self.threads}")
        logger.info("=" * 60)

        try:
            # Step 1: BLASTP
            logger.info("[STEP1] BLASTP 同源搜索...")
            self.homologs_fasta = run_blastp(
                self.query_fasta,
                self.database_dir,
                self.output_dir,
                self.threads,
                self.config,
            )

            # Step 2: cd-hit
            logger.info("[STEP2] cd-hit 去冗余...")
            self.cdhit_fasta = run_cdhit(
                self.homologs_fasta,
                self.output_dir,
                self.threads,
                self.config,
            )

            # Step 3: MAFFT
            logger.info("[STEP3] MAFFT 多序列比对...")
            self.aln_file = run_mafft(
                self.cdhit_fasta,
                self.output_dir,
                self.threads,
                self.config,
            )

            # Step 4: trimAl
            logger.info("[STEP4] trimAl 修剪...")
            self.trimal_aln = run_trimal(
                self.aln_file,
                self.output_dir,
                self.config,
            )

            # Step 5: 格式转换
            logger.info("[STEP5] 格式转换...")
            self.trimal_fasta = run_convert(
                self.trimal_aln,
                self.output_dir,
            )

            # Step 6: FastTree
            logger.info("[STEP6] FastTree 建树...")
            self.tree_file = run_fasttree(
                self.trimal_fasta,
                self.output_dir,
                self.threads,
                self.config,
            )

            # Step 7: 树注释
            logger.info("[STEP7] 树注释...")
            prefix = self.config.output_prefix or "result"
            run_annotation(
                self.trimal_fasta,
                prefix + "_TreeAnno",
                self.output_dir,
                self.config,
            )

            # Step 8: 统计
            logger.info("[STEP8] 基因计数统计...")
            run_stats(
                self.homologs_fasta,
                self.output_dir,
                self.config,
            )

            logger.info("=" * 60)
            logger.info("Pipeline 完成!")
            logger.info(f"进化树: {self.tree_file}")
            logger.info(f"注释: {prefix}_TreeAnno.xlsx")
            logger.info(f"统计: homologs_statics.xlsx")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Pipeline 执行失败: {e}")
            raise


def main():
    if len(sys.argv) < 4:
        print("Usage: python pipeline.py <query_fasta> <database_dir> <output_dir> [threads]")
        sys.exit(1)

    query_fasta = sys.argv[1]
    database_dir = sys.argv[2]
    output_dir = sys.argv[3]
    threads = int(sys.argv[4]) if len(sys.argv) > 4 else 16

    pipeline = Pipeline(query_fasta, database_dir, output_dir, threads)
    pipeline.run()


if __name__ == "__main__":
    main()
