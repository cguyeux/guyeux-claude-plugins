"""Non-régression du skill bacteria/hgt-interdomain-check (environnement/pistes.md AG2).

Trois familles de contrôles, toutes sur des jeux fabriqués dont la réponse est connue d'avance :

1. le parseur du tableau AU d'IQ-TREE lit bien la colonne `p-AU` et non sa voisine — les
   marqueurs `+`/`-` sont séparés par une espace dans la sortie réelle, et les laisser dans la
   liste décale silencieusement toutes les colonnes ;
2. `read_interdomain.py` REFUSE de conclure tant qu'une porte manque, et ne prononce un
   transfert que lorsque les quatre mesures convergent ;
3. la porte 0 rend PASSE sur une répétition indépendante franche, SUSPECT sur un assemblage
   unique sans autre anomalie, et BLOQUE quand l'assemblage unique s'accompagne d'une anomalie.
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "bacteria" / "skills" / "hgt-interdomain-check" / "scripts"
FRERE = ROOT / "bacteria" / "skills" / "hgt-direction-check" / "scripts"


def charge(nom):
    spec = importlib.util.spec_from_file_location(nom.replace(".py", ""), SKILL / nom)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lance(script, *args):
    r = subprocess.run([sys.executable, str(SKILL / script), *map(str, args)],
                       capture_output=True, text=True)
    return r


def verdict(sortie, cle):
    for l in sortie.splitlines():
        if l.startswith(cle + ":"):
            return l.split(":", 1)[1].strip()
    return None


# Tableau AU tel qu'IQ-TREE l'imprime réellement : marqueurs détachés, colonnes variables.
IQTREE_AU = """
USER TREES
----------

See http://www.iqtree.org/doc/Advanced-Tutorial for details.

Tree      logL    deltaL  bp-RELL    p-KH     p-SH    p-WKH    p-WSH       c-ELW       p-AU
-------------------------------------------------------------------------------------------
  1 -6424.38304       0   0.612 +  0.703 +      1 +  0.703 +      1 +     0.611 +    0.688 +
  2 -6431.11902  6.7360   0.388 +  0.297 +  0.297 +  0.297 +  0.297 +     0.389 +    0.312 +
  3 -6489.55110  65.168   0.001 -  0.004 -  0.004 -  0.004 -  0.004 -     0.001 -    0.003 -

deltaL  : logL difference from the maximal logl in the set.
"""

IQTREE_AU_DEUX_REJETS = """
USER TREES
----------

Tree      logL    deltaL  bp-RELL    p-KH     p-SH       c-ELW       p-AU
-------------------------------------------------------------------------
  1  -39471.9608       0   0.983 +  0.979 +      1 +     0.982 +        1 +
  2 -39524.14212  52.181  0.0174 - 0.0214 -  0.038 -    0.0181 -   0.0139 -
  3 -39608.51113  136.55       0 - 0.0001 - 0.0001 -  3.87e-06 - 2.18e-06 -

deltaL  : logL difference from the maximal logl in the set.
"""

ORDRE = ("ML_libre\tarbre ML sans contrainte\n"
         "H1_bacteries_monophyletiques\tpas de transfert\n"
         "H2_requete_dans_eucaryotes\ttransfert entre domaines\n")

# Arbre où QUERY est enfouie sous quatre plantes cohérentes, les bactéries restant à part.
ARBRE = ("((((QUERY,PLANT1)98.5/100,PLANT2)95/99,(PLANT3,PLANT4)90/97)88/95,"
         "(BACT1,(BACT2,BACT3)99/100)97/100);")
ARBRE_CTRL = "(((PLANT1,PLANT2)95/99,(PLANT3,PLANT4)90/97),(BACT1,(BACT2,BACT3)99/100));"
TAXONOMIE = ("QUERY\tBACTERIA\tLeptospira\n"
             "PLANT1\tEUKARYOTA\tViridiplantae\n"
             "PLANT2\tEUKARYOTA\tViridiplantae\n"
             "PLANT3\tEUKARYOTA\tViridiplantae\n"
             "PLANT4\tEUKARYOTA\tViridiplantae\n"
             "BACT1\tBACTERIA\tSpirochaetes\n"
             "BACT2\tBACTERIA\tSpirochaetes\n"
             "BACT3\tBACTERIA\tSpirochaetes\n")


class TestTableauAU(unittest.TestCase):
    def test_colonne_p_au_lue_et_pas_sa_voisine(self):
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            iq, ordre = Path(d) / "au.iqtree", Path(d) / "ordre.txt"
            iq.write_text(IQTREE_AU, encoding="utf-8")
            ordre.write_text(ORDRE, encoding="utf-8")
            res = topo.lit_au(iq, ordre, 0.05)
        self.assertEqual([r["nom"] for r in res],
                         ["ML_libre", "H1_bacteries_monophyletiques",
                          "H2_requete_dans_eucaryotes"])
        # p-AU, pas c-ELW (0,611) ni p-WSH (1) : c'est tout l'objet du contrôle.
        self.assertAlmostEqual(res[0]["p_AU"], 0.688)
        self.assertAlmostEqual(res[2]["p_AU"], 0.003)
        self.assertEqual([r["rejete"] for r in res], [False, False, True])
        self.assertAlmostEqual(res[1]["logL"], -6431.11902)
        self.assertAlmostEqual(res[1]["deltaL"], 6.7360)

    def test_tableau_sans_p_au_refuse(self):
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            iq, ordre = Path(d) / "au.iqtree", Path(d) / "ordre.txt"
            iq.write_text(IQTREE_AU.replace("p-AU", "p-XX"), encoding="utf-8")
            ordre.write_text(ORDRE, encoding="utf-8")
            with self.assertRaises(SystemExit):
                topo.lit_au(iq, ordre, 0.05)

    def test_ordre_incoherent_refuse_plutot_que_d_apparier_au_hasard(self):
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            iq, ordre = Path(d) / "au.iqtree", Path(d) / "ordre.txt"
            iq.write_text(IQTREE_AU, encoding="utf-8")
            ordre.write_text("ML_libre\tseul\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                topo.lit_au(iq, ordre, 0.05)

    def test_deux_rejets_ne_se_lisent_pas_comme_une_absence_de_signal(self):
        # Mesuré sur PF00856 (LIMLP_01555) : H1 et H2 imposent toutes deux une bipartition
        # GLOBALE des domaines, rejetée en soi dès que le domaine a une histoire réticulée.
        # Les deux sont alors rejetées sans que la requête y soit pour rien, et l'ancien
        # message « l'alignement ne tranche pas » était faux : il tranche, contre les deux.
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            iq, ordre, out = Path(d) / "au.iqtree", Path(d) / "ordre.txt", Path(d) / "v.txt"
            iq.write_text(IQTREE_AU_DEUX_REJETS, encoding="utf-8")
            ordre.write_text(ORDRE, encoding="utf-8")
            topo.commande_read(SimpleNamespace(iqtree=iq, order=ordre, seuil=0.05, out=out))
            texte = out.read_text(encoding="utf-8")
        self.assertIn("VERDICT_TOPOLOGIE: INDECIDABLE", texte)
        self.assertIn("Les DEUX hypothèses sont rejetées", texte)
        self.assertNotIn("Aucune des deux hypothèses n'est rejetée", texte)
        self.assertIn("84.4 unités de logL", texte)          # 136.55 - 52.18, l'écart utile
        self.assertIn("n'autorise PAS à retenir la moins rejetée", texte)


class TestLectureInterdomaine(unittest.TestCase):
    def prepare(self, d):
        chemins = {}
        for nom, contenu in (("arbre.nwk", ARBRE), ("ctrl.nwk", ARBRE_CTRL),
                             ("recode.nwk", ARBRE), ("tax.tsv", TAXONOMIE)):
            chemins[nom] = Path(d) / nom
            chemins[nom].write_text(contenu, encoding="utf-8")
        for nom, ligne in (("cont.txt", "VERDICT_CONTAMINATION: PASSE"),
                           ("comp.txt", "VERDICT_COMPOSITION: HETEROGENE"),
                           ("topo.txt", "VERDICT_TOPOLOGIE: TRANSFERT_SOUTENU"),
                           ("cont_bloque.txt", "VERDICT_CONTAMINATION: BLOQUE")):
            chemins[nom] = Path(d) / nom
            chemins[nom].write_text(ligne + "\n", encoding="utf-8")
        return chemins

    def test_quatre_mesures_convergentes_donnent_le_transfert(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.prepare(d)
            r = lance("read_interdomain.py", "--tree", c["arbre.nwk"],
                      "--tree-control", c["ctrl.nwk"], "--tree-recoded", c["recode.nwk"],
                      "--taxonomy", c["tax.tsv"], "--query", "QUERY",
                      "--contamination-report", c["cont.txt"],
                      "--composition-report", c["comp.txt"],
                      "--topology-report", c["topo.txt"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(verdict(r.stdout, "VERDICT_INTERDOMAINE"),
                         "TRANSFERT_INTER_DOMAINE_SOUTENU")

    def test_porte_manquante_interdit_tout_verdict(self):
        """Le défaut historique du skill frère : conclure quand un contrôle n'a pas tourné."""
        with tempfile.TemporaryDirectory() as d:
            c = self.prepare(d)
            for absent in ("--contamination-report", "--composition-report",
                           "--topology-report"):
                args = ["--tree", c["arbre.nwk"], "--tree-control", c["ctrl.nwk"],
                        "--tree-recoded", c["recode.nwk"], "--taxonomy", c["tax.tsv"],
                        "--query", "QUERY", "--contamination-report", c["cont.txt"],
                        "--composition-report", c["comp.txt"],
                        "--topology-report", c["topo.txt"]]
                i = args.index(absent)
                del args[i:i + 2]
                r = lance("read_interdomain.py", *args)
                self.assertEqual(verdict(r.stdout, "VERDICT_INTERDOMAINE"), "AUCUN_VERDICT",
                                 f"sans {absent}, un verdict a été prononcé")

    def test_arbre_recode_exige_des_que_la_composition_n_est_pas_homogene(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.prepare(d)
            r = lance("read_interdomain.py", "--tree", c["arbre.nwk"],
                      "--tree-control", c["ctrl.nwk"], "--taxonomy", c["tax.tsv"],
                      "--query", "QUERY", "--contamination-report", c["cont.txt"],
                      "--composition-report", c["comp.txt"],
                      "--topology-report", c["topo.txt"])
        self.assertEqual(verdict(r.stdout, "VERDICT_INTERDOMAINE"), "AUCUN_VERDICT")
        self.assertIn("recodé", r.stdout)

    def test_contamination_bloquante_prime_sur_la_topologie(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.prepare(d)
            r = lance("read_interdomain.py", "--tree", c["arbre.nwk"],
                      "--tree-control", c["ctrl.nwk"], "--tree-recoded", c["recode.nwk"],
                      "--taxonomy", c["tax.tsv"], "--query", "QUERY",
                      "--contamination-report", c["cont_bloque.txt"],
                      "--composition-report", c["comp.txt"],
                      "--topology-report", c["topo.txt"])
        self.assertEqual(verdict(r.stdout, "VERDICT_INTERDOMAINE"), "CONTAMINATION_PROBABLE")

    def test_socle_partage_et_non_recopie(self):
        """read_interdomain.py doit lire le Newick par le parseur du skill frère : c'est lui
        qui sait défaire le support composite `SH-aLRT/UFBoot`."""
        lecture = charge("read_interdomain.py")
        self.assertEqual(lecture.SOCLE_DEFAUT, FRERE / "read_direction.py")
        self.assertTrue(lecture.SOCLE_DEFAUT.exists())
        socle = lecture.charge_socle(lecture.SOCLE_DEFAUT)
        self.assertTrue(hasattr(socle, "lit_arbre") and hasattr(socle, "support"))


class TestPorteContamination(unittest.TestCase):
    def cas(self, lignes, *extra):
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "presence.tsv"
            tsv.write_text("".join(lignes), encoding="utf-8")
            r = lance("assembly_contamination_check.py", "--presence-tsv", tsv, *extra)
        return verdict(r.stdout, "VERDICT_CONTAMINATION"), r

    def test_repetition_franche_ouvre_la_porte(self):
        v, r = self.cas([f"GCA_{i:09d}.1\tLeptospira interrogans\n" for i in range(12)])
        self.assertEqual(v, "PASSE")
        # et le verdict ne doit pas s'attribuer des contrôles qu'il n'a pas faits
        self.assertIn("Non mesuré ici", r.stdout)

    def test_assemblage_unique_sans_autre_anomalie_reste_suspect(self):
        v, _ = self.cas(["GCA_000000001.1\tLeptospira interrogans\n"])
        self.assertEqual(v, "SUSPECT")

    def test_assemblage_unique_avec_couverture_aberrante_bloque(self):
        with tempfile.TemporaryDirectory() as d:
            tsv, cov = Path(d) / "p.tsv", Path(d) / "cov.tsv"
            tsv.write_text("GCA_000000001.1\tLeptospira interrogans\n", encoding="utf-8")
            cov.write_text("".join(f"ctg{i}\t100\n" for i in range(20))
                           + "ctg_suspect\t4000\n", encoding="utf-8")
            r = lance("assembly_contamination_check.py", "--presence-tsv", tsv,
                      "--coverage-tsv", cov, "--contig", "ctg_suspect")
        self.assertEqual(verdict(r.stdout, "VERDICT_CONTAMINATION"), "BLOQUE")

    def test_sans_mesure_de_repetition_le_script_refuse_de_tourner(self):
        r = lance("assembly_contamination_check.py")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("répétition indépendante", r.stderr)


class TestCompositionSaturation(unittest.TestCase):
    def ecrit(self, d, blocs):
        chemin = Path(d) / "aln.faa"
        chemin.write_text("".join(f">{n}\n{s}\n" for n, s in blocs), encoding="utf-8")
        return chemin

    def test_jeu_homogene(self):
        motif = "ACDEFGHIKLMNPQRSTVWY" * 5
        with tempfile.TemporaryDirectory() as d:
            aln = self.ecrit(d, [(f"S{i}", motif) for i in range(10)])
            r = lance("composition_saturation.py", "--alignment", aln)
        self.assertEqual(verdict(r.stdout, "VERDICT_COMPOSITION"), "HOMOGENE", r.stdout)

    def test_deux_compositions_opposees_sont_vues(self):
        a, b = "AAAAGGGGPPPPSSSS" * 6, "FFFFWWWWYYYYCCCC" * 6
        with tempfile.TemporaryDirectory() as d:
            aln = self.ecrit(d, [(f"A{i}", a) for i in range(6)]
                             + [(f"B{i}", b) for i in range(6)])
            r = lance("composition_saturation.py", "--alignment", aln)
        self.assertIn(verdict(r.stdout, "VERDICT_COMPOSITION"),
                      {"HETEROGENE", "HETEROGENE_ET_SATURE"}, r.stdout)

    def test_recodage_reduit_bien_l_alphabet(self):
        motif = "ACDEFGHIKLMNPQRSTVWY" * 5
        with tempfile.TemporaryDirectory() as d:
            aln = self.ecrit(d, [(f"S{i}", motif) for i in range(10)])
            sortie = Path(d) / "recode.faa"
            lance("composition_saturation.py", "--alignment", aln, "--recode", "sr4",
                  "--out-recoded", sortie)
            etats = set(sortie.read_text(encoding="utf-8").replace("\n", ""))
        self.assertTrue(etats <= set("0123->S") | set("0123456789"), etats)

    def test_focus_inconnu_refuse_plutot_que_de_chercher_par_le_contenu(self):
        motif = "ACDEFGHIKLMNPQRSTVWY" * 5
        with tempfile.TemporaryDirectory() as d:
            aln = self.ecrit(d, [(f"S{i}", motif) for i in range(5)])
            r = lance("composition_saturation.py", "--alignment", aln, "--focus", "ABSENTE")
        self.assertNotEqual(r.returncode, 0)


class TestPanelFromPfam(unittest.TestCase):
    """Fonctions pures du constructeur de panel : pas d'appel réseau dans les tests."""

    def entrees(self):
        # un genre écrasant (30 Legionella) et deux genres rares : exactement la configuration
        # qui a produit un faux transfert dans la littérature SET
        return ([{"acc": f"L{i}", "organisme": "Legionella pneumophila", "taxid": "446",
                  "seq": "A" * 200, "loc": (1, 100)} for i in range(30)]
                + [{"acc": "B1", "organisme": "Bacillus subtilis", "taxid": "1423",
                    "seq": "B" * 200, "loc": (1, 100)},
                   {"acc": "N1", "organisme": "Nostoc punctiforme", "taxid": "272131",
                    "seq": "C" * 200, "loc": (1, 100)}])

    def test_equilibrage_par_genre_brise_la_domination_d_un_genre(self):
        panel = charge("panel_from_pfam.py")
        retenus, n_genres = panel.echantillonne(self.entrees(), 2, 70, 1)
        self.assertEqual(n_genres, 3)
        genres = [e["organisme"].split()[0] for e in retenus]
        # 30 Legionella disponibles, 2 retenues : le plafond ne doit PAS servir à les
        # réintroduire, sinon le genre le mieux séquencé reprend toute la place.
        self.assertEqual(genres.count("Legionella"), 2)
        self.assertIn("Bacillus", genres)
        self.assertIn("Nostoc", genres)
        self.assertEqual(len(retenus), 4)

    def test_echantillonnage_reproductible_a_graine_fixe(self):
        panel = charge("panel_from_pfam.py")
        a, _ = panel.echantillonne(self.entrees(), 2, 10, 42)
        b, _ = panel.echantillonne(self.entrees(), 2, 10, 42)
        self.assertEqual([e["acc"] for e in a], [e["acc"] for e in b])

    def test_etiquette_sans_espace_ni_ponctuation(self):
        panel = charge("panel_from_pfam.py")
        e = panel.etiquette("BAC", "Q9X1J2", "Leptospira interrogans serovar Manilae")
        self.assertEqual(e, "BAC_Q9X1J2_Leptospira")
        self.assertNotIn(" ", e)
        self.assertEqual(panel.etiquette("EUK", "P1", "[Candida] glabrata"), "EUK_P1_Candida")


# --- AG3 : contraintes LOCALES (placement de la requête) -----------------------------------------
# Arbre de référence SANS la requête, construit pour que rien n'y soit monophylétique à l'échelle
# d'un domaine (le cas mesuré sur PF00856) : un congénère isolé parmi d'autres bactéries (LEP5),
# un eucaryote isolé (E_SOLO), deux clades eucaryotes séparés par des archées.
REF_LOCAL = ("(((LEP1,LEP2)90/99,(LEP3,LEP4)85/95)88/97,"
             "((B1,(B2,LEP5)70/80)60/70,(B3,(B4,E_SOLO)50/60)55/65)40/50,"
             "(((EA1,EA2)99/100,EA3)95/99,((EB1,EB2)97/100,(A1,A2)99/100)60/70)75/80);")
# Arbre libre : la requête nichée dans les congénères.
ML_LOCAL = REF_LOCAL.replace("(LEP1,LEP2)", "((LEP1,QUERY),LEP2)")
TAX_LOCAL = "".join(
    f"{n}\t{d}\t{g}\n" for n, d, g in
    [("QUERY", "BACTERIA", "Leptospira")]
    + [(f"LEP{i}", "BACTERIA", "Leptospira") for i in range(1, 6)]
    + [(f"B{i}", "BACTERIA", "Proteo") for i in range(1, 5)]
    + [(n, "EUKARYOTA", "Fungi") for n in ("EA1", "EA2", "EA3", "EB1", "EB2", "E_SOLO")]
    + [("A1", "ARCHAEA", "Eury"), ("A2", "ARCHAEA", "Eury")])


def table_au(lignes):
    """Tableau USER TREES minimal ; lignes = [(logL, deltaL, p_AU), ...]."""
    corps = "\n".join(
        f"  {i} {l:.3f} {d:.3f}   0.5 +  0.5 +  0.5 +     0.5 +  {p:.4g} {'+' if p >= 0.05 else '-'}"
        for i, (l, d, p) in enumerate(lignes, 1))
    return ("USER TREES\n----------\n\n"
            "Tree      logL    deltaL  bp-RELL    p-KH     p-SH       c-ELW       p-AU\n"
            "-------------------------------------------------------------------------\n"
            + corps + "\n\ndeltaL  : logL difference from the maximal logl in the set.\n")


class TestModeLocal(unittest.TestCase):
    def prepare(self, d, ref=REF_LOCAL):
        d = Path(d)
        feuilles = [l.split("\t")[0] for l in TAX_LOCAL.splitlines()]
        (d / "aln.fa").write_text("".join(f">{n}\nAAAA\n" for n in feuilles), encoding="utf-8")
        (d / "tax.tsv").write_text(TAX_LOCAL, encoding="utf-8")
        (d / "ref.nwk").write_text(ref, encoding="utf-8")
        (d / "ml.nwk").write_text(ML_LOCAL, encoding="utf-8")
        return d

    def genere(self, d, *extra):
        return lance("topology_test.py", "constraints", "--local", "--alignment", d / "aln.fa",
                     "--taxonomy", d / "tax.tsv", "--query", "QUERY",
                     "--reference-tree", d / "ref.nwk", "--ml-tree", d / "ml.nwk",
                     "--out", d / "out", *extra)

    def test_squelette_fixe_seul_le_clade_focal_change_de_place(self):
        """AG3, 2026-09-25 : arbres FIXÉS, squelette = référence privée du clade focal V_k,
        F = V_k + requête ; chaque hypothèse ne diffère que par le point d'attache de F."""
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            d = self.prepare(d)
            r = self.genere(d)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = d / "out"
            ordre = (out / "trees_order.txt").read_text(encoding="utf-8").splitlines()
            self.assertEqual(ordre[0], "#mode\tsquelette_fixe")
            noms = [l.split("\t")[0] for l in ordre[1:]]
            self.assertEqual(noms, ["HV1_focal_en_place_Leptospira_4",
                                    "HT1_focal_sur_eukaryota_3", "HT2_focal_sur_eukaryota_2"])
            # plus d'arbre ML dans le jeu : il diffère du squelette ailleurs et pénaliserait
            # tous les arbres fixés pour une raison étrangère au placement
            self.assertNotIn("ML_libre", "\n".join(ordre))
            self.assertNotIn(" -g ", (out / "commandes.sh").read_text())
            focal = frozenset({"QUERY", "LEP1", "LEP2", "LEP3", "LEP4"})
            ref = topo.lit_arbre(d / "ref.nwk")
            arbres = (out / "trees_local.nwk").read_text().strip().splitlines()
            self.assertEqual(len(arbres), 3)
            from Bio import Phylo
            lus = list(Phylo.parse(str(out / "trees_local.nwk"), "newick"))
            cotes = [topo.cotes_aretes(a)[1] for a in lus]
            for c in cotes:
                self.assertIn(focal, c)
            self.assertIn(focal | {"EA1", "EA2", "EA3"}, cotes[1])
            self.assertIn(focal | {"EB1", "EB2"}, cotes[2])
            # la requête reste où l'arbre ML la met parmi ses congénères
            for c in cotes:
                self.assertIn(frozenset({"QUERY", "LEP1"}), c)
            # V : la requête ôtée, on retrouve EXACTEMENT l'arbre de référence
            lus[0].prune("QUERY")
            self.assertEqual(topo.cotes_aretes(lus[0])[1], topo.cotes_aretes(ref)[1])
            for a in lus:
                self.assertEqual(len(a.root.clades), 3)      # non raciné pour IQ-TREE
            self.assertIn("contrôle « qui a bougé » passé", r.stdout)

    def test_donneur_deja_frere_du_clade_focal_repris_par_alias(self):
        # EA est le frère du clade Leptospira dans la référence : F sur la tige de EA et F à sa
        # place sont le MÊME arbre ; un doublon fausserait les p-AU sous RELL.
        ref = ("((((LEP1,LEP2),(LEP3,LEP4)),((EA1,EA2),EA3)),"
               "((B1,(B2,LEP5)),(B3,(B4,E_SOLO))),((EB1,EB2),(A1,A2)));")
        with tempfile.TemporaryDirectory() as d:
            d = self.prepare(d, ref=ref)
            (d / "ml.nwk").write_text(ref.replace("(LEP1,LEP2)", "((LEP1,QUERY),LEP2)"))
            r = self.genere(d)
            self.assertEqual(r.returncode, 0, r.stderr)
            ordre = (d / "out" / "trees_order.txt").read_text(encoding="utf-8").splitlines()
            ht1 = next(l for l in ordre if l.startswith("HT1_"))
            self.assertTrue(ht1.endswith("\t=HV1_focal_en_place_Leptospira_4"), ht1)
            self.assertEqual(len((d / "out" / "trees_local.nwk").read_text().split(";")) - 1, 2)

    def test_soeurs_ml_hors_clade_de_reference_greffe_sur_le_plus_proche_voisin(self):
        ml = REF_LOCAL.replace(
            "((LEP1,LEP2)90/99,(LEP3,LEP4)85/95)88/97",
            "(((LEP1:0.1,LEP3:0.5):0.1,QUERY:0.1):0.1,(LEP2:0.1,LEP4:0.1):0.1)")
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            d = self.prepare(d)
            (d / "ml.nwk").write_text(ml)
            r = self.genere(d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("plus proche voisin patristique", r.stdout)
            from Bio import Phylo
            for a in Phylo.parse(str(d / "out" / "trees_local.nwk"), "newick"):
                self.assertIn(frozenset({"QUERY", "LEP1"}), topo.cotes_aretes(a)[1])

    def test_controle_qui_a_bouge_detecte_un_autre_deplacement(self):
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            d = self.prepare(d)
            self.assertEqual(self.genere(d).returncode, 0)
            out = d / "out"
            lignes = (out / "trees_local.nwk").read_text().splitlines()
            # HT1 falsifié : un eucaryote isolé change aussi de place (E_SOLO <-> B2)
            lignes[1] = (lignes[1].replace("E_SOLO", "TMP").replace("B2", "E_SOLO")
                         .replace("TMP", "B2"))
            (out / "trees_local.nwk").write_text("\n".join(lignes) + "\n")
            iq, v = out / "au.iqtree", out / "v.txt"
            iq.write_text(table_au([(-100, 0, 0.98), (-160, 60, 0.001), (-150, 50, 0.004)]))
            topo.commande_read(SimpleNamespace(iqtree=iq, order=out / "trees_order.txt",
                                               seuil=0.05, out=v))
            texte = v.read_text(encoding="utf-8")
            self.assertIn("VERDICT_TOPOLOGIE: NON_VALIDE", texte)
            self.assertIn("autre chose que F a bougé", texte)

    def lit_fixe(self, lignes):
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            d = self.prepare(d)
            self.assertEqual(self.genere(d).returncode, 0)
            out = d / "out"
            iq, v = out / "au.iqtree", out / "v.txt"
            iq.write_text(table_au(lignes))
            topo.commande_read(SimpleNamespace(iqtree=iq, order=out / "trees_order.txt",
                                               seuil=0.05, out=v))
            return v.read_text(encoding="utf-8")

    def test_squelette_fixe_rend_un_verdict_consommable(self):
        texte = self.lit_fixe([(-100, 0, 0.98), (-160, 60, 0.001), (-150, 50, 0.004)])
        self.assertIn("VERDICT_TOPOLOGIE: VERTICAL_SOUTENU", texte)
        self.assertIn("Contrôle « qui a bougé » passé", texte)
        self.assertIn("conditionnel au squelette", texte)
        self.assertNotIn("SANS valeur de preuve", texte)

    def test_squelette_fixe_donneur_ouvert_rend_indecidable(self):
        texte = self.lit_fixe([(-100, 0, 0.9), (-101, 1, 0.4), (-150, 50, 0.004)])
        self.assertIn("VERDICT_TOPOLOGIE: INDECIDABLE", texte)
        self.assertIn("point d'attache du clade", texte)

    def test_squelette_fixe_lignee_rejetee_rend_le_transfert(self):
        texte = self.lit_fixe([(-170, 70, 0.0005), (-100, 0, 0.99), (-150, 50, 0.004)])
        self.assertIn("VERDICT_TOPOLOGIE: TRANSFERT_SOUTENU", texte)

    def test_squelette_fixe_sans_arbres_evalues_ne_conclut_pas(self):
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            d = self.prepare(d)
            self.assertEqual(self.genere(d).returncode, 0)
            out = d / "out"
            (out / "trees_local.nwk").rename(out / "ailleurs.nwk")
            iq, v = out / "au.iqtree", out / "v.txt"
            iq.write_text(table_au([(-100, 0, 0.98), (-160, 60, 0.001), (-150, 50, 0.004)]))
            topo.commande_read(SimpleNamespace(iqtree=iq, order=out / "trees_order.txt",
                                               seuil=0.05, out=v))
            self.assertIn("VERDICT_TOPOLOGIE: NON_VALIDE", v.read_text(encoding="utf-8"))

    def test_arbres_manquants_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            d = self.prepare(d)
            r = lance("topology_test.py", "constraints", "--local", "--alignment", d / "aln.fa",
                      "--taxonomy", d / "tax.tsv", "--query", "QUERY", "--out", d / "out")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("--reference-tree", r.stderr)

    def test_arbre_de_reference_contenant_la_requete_refuse(self):
        # Lire les ensembles sur l'arbre qui contient la requête serait circulaire.
        with tempfile.TemporaryDirectory() as d:
            d = self.prepare(d, ref=ML_LOCAL)
            r = self.genere(d)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("SANS la requête", r.stderr)

    def test_clade_donneur_qui_n_est_pas_un_clade_refuse(self):
        with tempfile.TemporaryDirectory() as d:
            d = self.prepare(d)
            r = self.genere(d, "--donor-clade", "EA1,EB1")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("ne forme pas un clade", r.stderr)

    def lit(self, lignes, ordre):
        topo = charge("topology_test.py")
        with tempfile.TemporaryDirectory() as d:
            iq, o, out = Path(d) / "au.iqtree", Path(d) / "ordre.txt", Path(d) / "v.txt"
            iq.write_text(table_au(lignes), encoding="utf-8")
            o.write_text(ordre, encoding="utf-8")
            res = topo.lit_au(iq, o, 0.05)
            topo.commande_read(SimpleNamespace(iqtree=iq, order=o, seuil=0.05, out=out))
            return res, out.read_text(encoding="utf-8")

    # Ancien mode local (contrainte partielle, sans marqueur #mode) : lecture NON_VALIDE conservée
    # pour relire les sorties du 2026-09-24.
    ORDRE_ALIAS = ("ML_libre\tML\tlibre\tarbre\n"
                   "HV1\tV\tlignée\t=ML_libre\n"
                   "HT1\tT\teucaryotes A\tarbre\n"
                   "HT2\tT\teucaryotes B\tarbre\n")

    def test_alias_herite_du_p_au_de_l_arbre_ml_et_verdict_vertical(self):
        res, texte = self.lit([(-100, 0, 0.98), (-160, 60, 0.001), (-150, 50, 0.004)],
                              self.ORDRE_ALIAS)
        hv1 = next(r for r in res if r["nom"] == "HV1")
        self.assertAlmostEqual(hv1["p_AU"], 0.98)
        self.assertFalse(hv1["rejete"])
        self.assertIn("VERDICT_TOPOLOGIE: NON_VALIDE", texte)
        self.assertIn("SANS valeur de preuve : VERTICAL_SOUTENU", texte)
        self.assertIn("mode LOCAL", texte)

    def test_un_placement_eucaryote_non_rejete_rend_indecidable(self):
        _res, texte = self.lit([(-100, 0, 0.9), (-101, 1, 0.4), (-150, 50, 0.004)],
                               self.ORDRE_ALIAS)
        self.assertIn("SANS valeur de preuve : INDECIDABLE", texte)
        self.assertIn("Au moins un placement de chaque famille", texte)

    def test_lignee_rejetee_et_eucaryote_ouvert_rend_le_transfert(self):
        ordre = ("ML_libre\tML\tlibre\tarbre\n"
                 "HV1\tV\tlignée\tarbre\n"
                 "HT1\tT\teucaryotes A\t=ML_libre\n")
        _res, texte = self.lit([(-100, 0, 0.99), (-170, 70, 0.0005)], ordre)
        self.assertIn("SANS valeur de preuve : TRANSFERT_SOUTENU", texte)

    def test_tout_rejete_n_est_pas_lu_comme_artefact_des_contraintes(self):
        ordre = ("ML_libre\tML\tlibre\tarbre\n"
                 "HV1\tV\tlignée\tarbre\n"
                 "HT1\tT\teucaryotes A\tarbre\n")
        _res, texte = self.lit([(-100, 0, 1.0), (-140, 40, 0.003), (-180, 80, 0.0001)], ordre)
        self.assertIn("SANS valeur de preuve : INDECIDABLE", texte)
        self.assertIn("TOUS les placements testés sont rejetés", texte)
        self.assertIn("reste REJETÉ", texte)

    def test_alias_ne_compte_pas_dans_l_appariement(self):
        # 3 arbres testés, 4 lignes d'ordre dont un alias : l'appariement doit tenir.
        res, _t = self.lit([(-100, 0, 0.98), (-160, 60, 0.001), (-150, 50, 0.004)],
                           self.ORDRE_ALIAS)
        self.assertEqual([r["nom"] for r in res], ["ML_libre", "HV1", "HT1", "HT2"])
        self.assertAlmostEqual(res[3]["p_AU"], 0.004)

    def test_ancien_mode_local_ne_rend_jamais_un_verdict_consommable(self):
        """AG3, 2026-09-25 : la contrainte {requête} ∪ C se satisfait en déplaçant C, pas la
        requête ; un VERTICAL_SOUTENU local ferait conclure read_interdomain.py à tort."""
        _res, texte = self.lit([(-100, 0, 0.98), (-160, 60, 0.001), (-150, 50, 0.004)],
                               self.ORDRE_ALIAS)
        self.assertNotIn("VERDICT_TOPOLOGIE: VERTICAL_SOUTENU", texte)
        self.assertIn("c'est C qui bouge", texte)


class TestAppuiDuVerdictPropre(unittest.TestCase):
    """AG3, 2026-09-25 : « la requête se range dans son domaine, OU le test AU rejette » laissait
    croire que le test AU avait tranché alors qu'il était indécidable."""
    ARBRE_PROPRE = ("((((QUERY,BACT1)98/100,BACT2)95/99,BACT3)90/97,"
                    "((PLANT1,PLANT2)95/99,(PLANT3,PLANT4)90/97)88/95);")

    def test_verdict_propre_sans_test_au_concluant_dit_sur_quoi_il_repose(self):
        with tempfile.TemporaryDirectory() as d:
            c = {}
            for nom, contenu in (("arbre.nwk", self.ARBRE_PROPRE), ("tax.tsv", TAXONOMIE),
                                 ("ctrl.nwk", self.ARBRE_PROPRE.replace("(QUERY,BACT1)98/100", "BACT1")),
                                 ("cont.txt", "VERDICT_CONTAMINATION: PASSE\n"),
                                 ("comp.txt", "VERDICT_COMPOSITION: HOMOGENE\n"),
                                 ("topo.txt", "VERDICT_TOPOLOGIE: NON_VALIDE\n")):
                c[nom] = Path(d) / nom
                c[nom].write_text(contenu, encoding="utf-8")
            r = lance("read_interdomain.py", "--tree", c["arbre.nwk"],
                      "--tree-control", c["ctrl.nwk"], "--taxonomy", c["tax.tsv"],
                      "--query", "QUERY", "--contamination-report", c["cont.txt"],
                      "--composition-report", c["comp.txt"], "--topology-report", c["topo.txt"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(verdict(r.stdout, "VERDICT_INTERDOMAINE"), "ORIGINE_PROPRE_AU_DOMAINE")
        self.assertIn("repose sur ce SEUL", r.stdout)
        self.assertNotIn("ou le test AU rejette", r.stdout)


if __name__ == "__main__":
    unittest.main()
