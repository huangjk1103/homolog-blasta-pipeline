#!/usr/bin/env python3
# coding = utf-8
"""
断点状态检查工具

【用法】
    python check_status.py --output /path/to/output/

【功能】
    检查各 Step 是否完成，输出完成状态和树文件统计
"""

import sys
import os
import argparse
from pathlib import Path

STEP_NAMES = {
    "step1_blastp": "BLASTP 同源搜索",
    "step2_cdhit": "cd-hit 去冗余",
    "step3_mafft": "MAFFT 比对",
    "step4_trimal": "trimAl 修剪",
    "step5_convert": "格式转换",
    "step6_fasttree": "FastTree 建树",
    "step7_annotation": "树注释",
    "step8_stats": "基因统计",
}


def check_status(output_dir: str):
    """检查输出目录的断点状态"""
    output_path = Path(output_dir)
    done_files = list(output_path.glob(".step*_done"))

    print(f"\n{'='*50}")
    print(f"Pipeline 状态检查: {output_dir}")
    print(f"{'='*50}")

    all_done = True
    for step_file, step_desc in STEP_NAMES.items():
        marker = output_path / f".{step_file}_done"
        if marker.exists():
            print(f"  ✅ [{step_file}] {step_desc} - 完成")
        else:
            print(f"  ❌ [{step_file}] {step_desc} - 未完成")
            all_done = False

    # 检查最终结果
    tree_file = output_path / "result.treefile"
    if tree_file.exists():
        print(f"\n  🏁 进化树文件: {tree_file}")
        print(f"     大小: {tree_file.stat().st_size} bytes")
        # 简单统计树中节点数
        with open(tree_file, "r") as f:
            content = f.read().strip()
            # Newick 格式：统计分号数量
            node_count = content.count(",") + 1
            print(f"     节点数: ~{node_count}")

    anno_file = list(output_path.glob("*_TreeAnno.xlsx"))
    if anno_file:
        print(f"  📊 注释文件: {anno_file[0].name}")

    stat_file = output_path / "homologs_statics.xlsx"
    if stat_file.exists():
        print(f"  📈 统计文件: {stat_file.name}")

    print(f"{'='*50}")
    if all_done:
        print("  🎉 Pipeline 全部完成!")
    else:
        print("  ⚠️  Pipeline 未完成，可从断点继续运行")
    print()

    return all_done


def main():
    parser = argparse.ArgumentParser(description="检查 Pipeline 断点状态")
    parser.add_argument("--output", required=True, help="输出目录路径")
    args = parser.parse_args()

    if not os.path.isdir(args.output):
        print(f"错误: 目录不存在: {args.output}")
        sys.exit(1)

    check_status(args.output)


if __name__ == "__main__":
    main()
