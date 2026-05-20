# Homolog-Blast Pipeline

通用基因组同源基因分析全自动化 Pipeline。

从单条查询序列出发，自动完成：**BLASTP 同源搜索 → cd-hit 去冗余 → MAFFT 多序列比对 → trimAl 修剪 → FastTree 进化树构建 → 树注释 → 统计报告**

![Pipeline](https://img.shields.io/badge/Pipeline-8%20steps-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 流程图

```
查询序列 (FASTA)
    │
    ▼
[Step 1] BLASTP ── 同源搜索 ──→ homologs.fasta
    │                                  │
    ▼                                  │
[Step 2] cd-hit ── 去冗余 ──────────→ homologs.cdhit.fasta
    │                                  │
    ▼                                  │
[Step 3] MAFFT ── 多序列比对 ────→ homologs.aln (Clustal)
    │                                  │
    ▼                                  │
[Step 4] trimAl ── 修剪 ──────────→ homologs.trimal.{aln/fasta}
    │                                  │
    ▼                                  │
[Step 5] convert ── 格式转换 ────→ homologs.trimal.fasta (FASTA)
    │                                  │
    ▼                                  │
[Step 6] FastTree ── 建树 ───────→ result.treefile (Newick)
    │                                  │
    ├──[Step 7] annotation ──→ *_TreeAnno.xlsx
    │
    └──[Step 8] stats ──────────→ homologs_statics.xlsx
```

---

## 目录结构

```
homolog-blasta-pipeline/
├── pipeline/                  # Pipeline 核心模块
│   ├── __init__.py
│   ├── config.py             # 配置类 PipelineConfig
│   ├── pipeline.py           # 主编排器（断点续传）
│   ├── step1_blastp.py       # BLASTP 并行搜索
│   ├── step2_cdhit.py        # cd-hit 去冗余
│   ├── step3_mafft.py        # MAFFT 多序列比对
│   ├── step4_trimal.py        # trimAl 修剪
│   ├── step5_convert.py       # Clustal → FASTA 转换
│   ├── step6_fasttree.py      # FastTree 建树
│   ├── step7_annotation.py    # 树注释 XLSX 生成
│   └── step8_stats.py         # 基因计数统计
├── scripts/                   # 命令行工具
│   ├── run_pipeline.py       # Pipeline 运行入口
│   └── check_status.py        # 断点状态检查
└── README.md
```

---

## 安装依赖

### 系统依赖

```bash
# Debian/Ubuntu
sudo apt install ncbi-blast+ cd-hit mafft fasttree trimal

# 或通过 conda
conda install -c bioconda blast cd-hit mafft fasttree trimal
```

### Python 依赖

```bash
pip install biopython openpyxl pandas
```

---

## 使用方法

### 基础用法

```bash
python scripts/run_pipeline.py \
    --query /path/to/query.fasta \
    --database /path/to/database/ \
    --output /path/to/output/ \
    --threads 32
```

### 完整参数

```bash
python scripts/run_pipeline.py \
    --query /path/to/query.fasta \
    --database /path/to/database/ \
    --output /path/to/output/ \
    --threads 32 \
    --coverage 0.7 \
    --evalue 1e-5 \
    --cdhit 0.8 \
    --mafft-iterations 1000 \
    --bootstrap 100 \
    --prefix my_gene
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--query` | 必填 | 查询序列 FASTA 文件 |
| `--database` | 必填 | BLAST 数据库目录（内含 .faa 文件）|
| `--output` | 必填 | 输出目录 |
| `--threads` | 16 | BLASTP 并行线程数 |
| `--coverage` | 0.7 | BLASTP coverage 阈值 (0.0-1.0) |
| `--evalue` | 1e-5 | BLASTP E-value 阈值 |
| `--cdhit` | 0.8 | cd-hit 相似性阈值 |
| `--mafft-iterations` | 1000 | MAFFT 最大迭代次数 |
| `--bootstrap` | 100 | FastTree bootstrap 次数 |
| `--prefix` | homolog_analysis | 输出文件前缀 |

### 断点续传

Pipeline 支持断点续传，中断后可从断点继续：

```bash
# 检查断点状态
python scripts/check_status.py --output /path/to/output/

# 重新运行会自动从断点继续
python scripts/run_pipeline.py --query ... --database ... --output /path/to/output/
```

---

## 输入文件格式

### 查询序列 FASTA

标准 FASTA 格式，支持单条或多条序列：

```fasta
>T1NAG_00113
MFKLVILLGAAGIIGGTIAQSLKTVECQVLTNQNQQLAA...
```

### BLAST 数据库目录

目录内包含 `.faa` 蛋白序列文件，每个文件对应一个基因组：

```
database/
├── genome1.faa
├── genome2.faa
└── ...
```

### 分类注释文件（用于树注释）

通过 `config.py` 中的 `taxonomy_file` 配置，默认路径：
`/mnt/d/linux/1296_genome/homolog_blastp/phylogentic_tree_annotation.txt`

格式（Tab 分隔）：

```
GenomeID    Phylum           Class            Order             Family           Genus            Species
1296_0001   Planctomycetota  Planctomycetia   Planctomycetales  Planctomycetaceae Candidatus       Planctomyces
```

---

## 输出文件

| 文件 | 说明 |
|------|------|
| `homologs.fasta` | BLASTP 同源搜索结果 |
| `homologs.cdhit.fasta` | cd-hit 去冗余后的序列 |
| `homologs.aln` | MAFFT 比对结果 (Clustal 格式) |
| `homologs.trimal.aln` | trimAl 修剪后的比对 (Clustal) |
| `homologs.trimal.fasta` | trimAl 修剪后的序列 (FASTA) |
| `result.treefile` | FastTree 进化树 (Newick 格式) |
| `*_TreeAnno.xlsx` | 树注释表格 (Excel) |
| `homologs_statics.xlsx` | 基因计数统计报告 |

---

## PipelineConfig 配置类

可通过 `config.py` 修改默认参数：

```python
@dataclass
class PipelineConfig:
    taxonomy_file: str = "/path/to/phylogentic_tree_annotation.txt"
    min_seq_length: int = 10
    evalue: float = 1e-5
    coverage: float = 0.7
    blast_threads_per_db: int = 4
    cdhit_identity: float = 0.8
    mafft_iterations: int = 1000
    mafft_strategy: str = "localpair"
    trimal_strategy: str = "automated1"
    bootstrap: int = 100
    fasttree_model: str = "WAG"
    fasttree_seed: int = 1253
    output_prefix: str = "homolog_analysis"
```

---

## 交互式可视化

配套的 HTML 可视化工具：[homolog_viewer.html](https://github.com/huangjk1103/homolog-blasta-pipeline/blob/main/homolog_viewer.html)

在浏览器中打开，支持：
- 多序列比对 (MSA) 展示 + SVG 下载
- BLASTP 结果表格 + SVG 柱状图下载
- 进化树展示（门级别着色）+ SVG 下载
- 注释文件在线编辑 + 导出

---

## License

MIT License
