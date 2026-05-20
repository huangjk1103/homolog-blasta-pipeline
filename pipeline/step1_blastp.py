# coding = utf-8
"""
Step 1: BLASTP 并行同源搜索

【输入】
    - query_fasta: str, 查询序列 FASTA 文件路径
    - database_dir: str, BLAST 数据库目录（包含多个 .faa 或 .fa 文件）
    - config: PipelineConfig, 配置参数
    - threads: int, 总线程数（均分到各数据库）

【输出】
    - homologs.fasta: str, 所有同源基因序列（合并后）
    - .step1_blastp_done: str, 断点标记文件

【修复的 Bug】
    - 原始代码用 split('/t') 分割，正确的是 split('\\t')

【原理】
    1. 遍历 database_dir 下所有数据库文件
    2. 对每个数据库并行执行 blastp
    3. 过滤条件: coverage >= threshold AND evalue <= evalue_threshold
    4. 通过 blastdbcmd 提取满足条件的序列
    5. 合并所有同源序列到 homologs.fasta
"""

from Bio import SeqIO
import os
import sys
import multiprocessing
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple

# 导入配置
sys.path.insert(0, str(Path(__file__).parent))
from config import PipelineConfig, default_config

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_sequence_length(fasta_file: str) -> dict:
    """读取 FASTA 文件，返回 {seq_id: length}"""
    lengths = {}
    for seq_record in SeqIO.parse(fasta_file, "fasta"):
        lengths[seq_record.id] = len(seq_record)
    return lengths


def process_single_database(args: Tuple[str, str, str, PipelineConfig, int]) -> List[str]:
    """
    处理单个 BLAST 数据库
    返回: 提取到的同源序列 ID 列表
    """
    query_fasta, db_path, output_dir, config, query_len = args

    db_name = Path(db_path).stem
    blast_out = os.path.join(output_dir, f"{db_name}.tmp.blast")
    tmp_list = os.path.join(output_dir, f"{db_name}.tmp.list")
    tmp_fasta = os.path.join(output_dir, f"{db_name}_tmp.fasta")
    homolog_ids = []

    try:
        # Step 1: 执行 BLASTP
        cmd = config.get_blastp_cmd(query_fasta, db_path, blast_out, config.blast_threads_per_db)
        logger.info(f"  Running BLASTP on {db_name}...")
        subprocess.run(cmd, shell=True, check=True, capture_output=True)

        # Step 2: 解析结果，过滤 coverage
        if not os.path.exists(blast_out):
            logger.warning(f"  No BLAST output for {db_name}")
            return []

        with open(tmp_list, "w") as list_file:
            with open(blast_out, "r") as blast_data:
                for line in blast_data:
                    # 关键修复: 用 \t 分割，不用 /t
                    fields = line.strip().split("\t")
                    if len(fields) < 12:
                        continue
                    try:
                        q_start = int(fields[6])
                        q_end = int(fields[7])
                        match_len = q_end - q_start
                        coverage = float(match_len) / float(query_len)
                        evalue = float(fields[10])

                        if coverage >= config.coverage and evalue <= config.evalue:
                            list_file.write(fields[1] + "\n")
                            homolog_ids.append(fields[1])
                    except (ValueError, IndexError) as e:
                        logger.warning(f"  Parse error in {db_name}: {e}")
                        continue

        # Step 3: 提取序列
        if homolog_ids and os.path.exists(tmp_list):
            with open(tmp_list, "r") as list_file:
                ids_content = list_file.read()
            if ids_content.strip():
                extract_cmd = f"blastdbcmd -entry_batch {tmp_list} -db {db_path} -out {tmp_fasta}"
                subprocess.run(extract_cmd, shell=True, check=True, capture_output=True)

                # 清理临时文件
                if os.path.exists(tmp_fasta):
                    os.remove(tmp_fasta)
            os.remove(tmp_list)

        # 清理 BLAST 输出
        if os.path.exists(blast_out):
            os.remove(blast_out)

        logger.info(f"  {db_name}: found {len(homolog_ids)} homologs")
        return homolog_ids

    except subprocess.CalledProcessError as e:
        logger.error(f"  Error processing {db_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"  Unexpected error in {db_name}: {e}")
        return []


def run_blastp(
    query_fasta: str,
    database_dir: str,
    output_dir: str,
    threads: int = 16,
    config: PipelineConfig = None,
) -> str:
    """
    运行 BLASTP 同源搜索主函数

    Args:
        query_fasta: 查询序列文件路径
        database_dir: BLAST 数据库目录
        output_dir: 输出目录
        threads: 总线程数
        config: 配置对象

    Returns:
        homologs.fasta 文件路径
    """
    if config is None:
        config = default_config

    os.makedirs(output_dir, exist_ok=True)

    # 检查断点
    checkpoint_file = os.path.join(output_dir, ".step1_blastp_done")
    if os.path.exists(checkpoint_file):
        homolog_fasta = os.path.join(output_dir, "homologs.fasta")
        if os.path.exists(homolog_fasta):
            logger.info(f"[STEP1] Resume: homologs.fasta already exists at {homolog_fasta}")
            return homolog_fasta

    # 获取查询序列长度（支持多条序列，取最短的作为参考）
    seq_lengths = get_sequence_length(query_fasta)
    query_len = min(seq_lengths.values()) if seq_lengths else 0
    logger.info(f"[STEP1] Query: {query_fasta}, {len(seq_lengths)} sequences, min length: {query_len}")

    # 收集所有数据库文件
    db_files = []
    for ext in ["*.faa", "*.fa", "*.faa.gz"]:
        db_files.extend(Path(database_dir).glob(ext))

    logger.info(f"[STEP1] Found {len(db_files)} databases")

    if not db_files:
        raise FileNotFoundError(f"No database files found in {database_dir}")

    # 构建参数列表（每条 query 序列 × 每个数据库）
    tasks = []
    for db_path in db_files:
        tasks.append((query_fasta, str(db_path), output_dir, config, query_len))

    # 并行处理
    num_workers = min(len(db_files), threads)
    logger.info(f"[STEP1] Starting {num_workers} parallel workers...")

    all_homolog_ids = []
    with multiprocessing.Pool(processes=num_workers) as pool:
        results = pool.map(process_single_database, tasks)
        for ids in results:
            all_homolog_ids.extend(ids)

    # 去重
    all_homolog_ids = list(set(all_homolog_ids))
    logger.info(f"[STEP1] Total unique homologs: {len(all_homolog_ids)}")

    # 写入选中 ID 列表文件
    homolog_list_file = os.path.join(output_dir, "homolog_ids.txt")
    with open(homolog_list_file, "w") as f:
        for hid in all_homolog_ids:
            f.write(hid + "\n")

    # 为每个数据库执行序列提取（因为需要从各自的数据库提取）
    # 合并所有数据库的同源序列
    final_fasta = os.path.join(output_dir, "homologs.fasta")
    query_seqs = list(SeqIO.parse(query_fasta, "fasta"))
    with open(final_fasta, "w") as out_fasta:
        # 先写入查询序列本身
        for seq in query_seqs:
            SeqIO.write(seq, out_fasta, "fasta")

        # 再从各数据库提取同源序列
        for db_path in db_files:
            db_name = Path(db_path).stem
            tmp_fasta = os.path.join(output_dir, f"{db_name}_tmp.fasta")

            # 找出该数据库的同源 ID
            db_homolog_ids = [hid for hid in all_homolog_ids if True]  # 先收集，后面按数据库过滤

            # 重新解析 BLAST 结果找到属于该数据库的 ID
            db_ids = set()
            blast_out = os.path.join(output_dir, f"{db_name}.tmp.blast")
            if os.path.exists(blast_out):
                with open(blast_out, "r") as bf:
                    for line in bf:
                        fields = line.strip().split("\t")
                        if len(fields) < 12:
                            continue
                        try:
                            q_start = int(fields[6])
                            q_end = int(fields[7])
                            coverage = float(q_end - q_start) / float(query_len)
                            evalue = float(fields[10])
                            if coverage >= config.coverage and evalue <= config.evalue:
                                db_ids.add(fields[1])
                        except:
                            continue

            if db_ids:
                # 构建临时列表文件
                list_file = os.path.join(output_dir, f"{db_name}.ids.tmp")
                with open(list_file, "w") as lf:
                    for hid in db_ids:
                        lf.write(hid + "\n")

                # 提取序列
                extract_cmd = f"blastdbcmd -entry_batch {list_file} -db {db_path} -out {tmp_fasta}"
                subprocess.run(extract_cmd, shell=True, check=True, capture_output=True)

                # 合并到最终文件
                if os.path.exists(tmp_fasta):
                    for seq in SeqIO.parse(tmp_fasta, "fasta"):
                        SeqIO.write(seq, out_fasta, "fasta")
                    os.remove(tmp_fasta)
                os.remove(list_file)

    # 创建断点标记
    Path(checkpoint_file).touch()

    logger.info(f"[STEP1] Done! Output: {final_fasta}")
    return final_fasta


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python step1_blastp.py <query_fasta> <database_dir> <output_dir> [threads]")
        sys.exit(1)

    query_fasta = sys.argv[1]
    database_dir = sys.argv[2]
    output_dir = sys.argv[3]
    threads = int(sys.argv[4]) if len(sys.argv) > 4 else 16

    run_blastp(query_fasta, database_dir, output_dir, threads)
