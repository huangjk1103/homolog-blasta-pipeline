from dataclasses import dataclass


@dataclass
class PipelineConfig:
    taxonomy_file: str = "/mnt/d/linux/1296_genome/homolog_blastp/phylogentic_tree_annotation.txt"
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

    def get_mafft_cmd(self) -> str:
        strategy_map = {
            "localpair": "--localpair --maxiterate",
            "gthread": "--globalpair --thread 4",
            "fft": "--auto",
        }
        strategy = strategy_map.get(self.mafft_strategy, "--localpair --maxiterate")
        return f"mafft {strategy} {self.mafft_iterations}"

    def get_blastp_cmd(self, query: str, db: str, out: str, threads: int) -> str:
        return (
            f"blastp -query {query} -db {db} -out {out} "
            f"-num_threads {threads} "
            f"-evalue {self.evalue} "
            f"-outfmt '6 qseqid sseqid pident length mismatch gapopen "
            f"qstart qend sstart send evalue bitscore qcovhsp'"
        )


default_config = PipelineConfig()
