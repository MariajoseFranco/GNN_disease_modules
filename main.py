import pandas as pd
from tqdm import tqdm

from classical_methods.diamond_algorithm import DIAMOND
from classical_methods.domino_algorithm import DOMINO
from classical_methods.lcc_algorithm import LCC
from classical_methods.robust_algorithm import ROBUST
from classical_methods.topas_algorithm import TOPAS
from data_compilation import DataCompilation
from graph_creation import GraphPPI
from visualization import VisualizationModule


class Main():
    def __init__(self, path):
        # Select the diseases to work with
        self.selected_diseases = ["Albinism", "Alcohol Use Disorder"]
        self.DC = DataCompilation(path, self.selected_diseases)
        self.GPPI = GraphPPI()
        self.V = VisualizationModule()
        self.LCC = LCC()
        self.DIAMOND = DIAMOND()
        self.DOMINO = DOMINO()
        self.ROBUST = ROBUST()
        self.TOPAS = TOPAS()

    def run_classical_methods(self, G_ppi, disease_pro_mapping, MIN_SEEDS=10):
        results = {}

        for disease, all_seeds in tqdm(disease_pro_mapping.items()):
            print(f"Processing: {disease} ({len(all_seeds)} raw seeds)")

            seed_nodes = [node for node in all_seeds if node in G_ppi]
            if len(seed_nodes) < MIN_SEEDS:
                print("Skipped — not enough seeds in PPI")
                continue

            results[disease] = {}

            try:
                results[disease]["lcc"] = list(
                    self.LCC.run_lcc(
                        G_ppi,
                        seed_nodes
                    ).nodes
                )
            except Exception as e:
                print("LCC failed:", e)

            try:
                results[disease]["topas"] = list(
                    self.TOPAS.run_topas(
                        G_ppi,
                        seed_nodes,
                        max_dist=3,
                        top_percent=0.3
                    )
                )
            except Exception as e:
                print("TOPAS failed:", e)

            try:
                results[disease]["diamond"] = list(
                    self.DIAMOND.run_diamond(
                        G_ppi,
                        seed_nodes,
                        num_iterations=100
                    )
                )
            except Exception as e:
                print("DIAMOnD failed:", e)

            try:
                results[disease]["domino"] = list(
                    self.DOMINO.run_domino(
                        G_ppi,
                        seed_nodes
                    )
                )
            except Exception as e:
                print("DOMINO failed:", e)

            try:
                results[disease]["robust"] = list(
                    self.ROBUST.run_robust_fallback(
                        G_ppi,
                        seed_nodes,
                        n_trees=30
                    )
                )
            except Exception as e:
                print("ROBUST failed:", e)
        return results

    def save_classical_methods_results(self, results):
        all_modules = []

        for disease, methods in results.items():
            for method, gene_list in methods.items():
                for gene in gene_list:
                    all_modules.append({
                        "disease": disease,
                        "method": method,
                        "protein_id": gene
                    })

        pd.DataFrame(all_modules).to_csv("./outputs/multi_disease_modules.csv", index=False)
        print("Saved all modules to 'multi_disease_modules.csv'")

    def visualize_disease_results(
            self, disease, G_ppi, disease_pro_mapping, results
    ):
        # Seed Gene Subgraph
        self.V.visualize_seed_gene_subgraph(
            disease, G_ppi, disease_pro_mapping
        )

        # LCC
        self.V.visualize_module(
            "lcc",
            G_ppi,
            results[disease]["lcc"],
            disease,
            seed_nodes=list(disease_pro_mapping[disease])
        )
        # DIAMOND
        self.V.visualize_diamond_module(
            G_ppi,
            results[disease]["diamond"],
            disease_pro_mapping[disease],
            disease
        )
        # DOMINO
        self.V.visualize_domino_module(
            G_ppi,
            results[disease]["domino"],
            disease_pro_mapping[disease],
            disease
        )
        # ROBUST
        self.V.visualize_module(
            "robust",
            G_ppi,
            results[disease]["robust"],
            disease,
            seed_nodes=list(disease_pro_mapping[disease])
        )
        # TOPAS
        self.V.visualize_module(
            "topas",
            G_ppi,
            results[disease]["topas"],
            disease,
            seed_nodes=list(disease_pro_mapping[disease])
        )

    def main(self):
        df_pro_pro, df_gen_pro, df_dis_gen, df_dis_pro = self.DC.main()
        G_ppi, disease_pro_mapping = self.GPPI.main(df_pro_pro, df_dis_pro)
        results_classical_methods = self.run_classical_methods(G_ppi, disease_pro_mapping)
        self.save_classical_methods_results(results_classical_methods)
        for disease in self.selected_diseases:
            self.visualize_disease_results(
                disease, G_ppi, disease_pro_mapping, results_classical_methods
            )


if __name__ == "__main__":
    path = "./data/"
    # path = "/app/data/"
    Main(path).main()
