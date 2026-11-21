# Projet Advanced Algorithms — Minimum Set Cover

## 1. Introduction

Le problème étudié est le **Minimum (Unicost) Set Cover Problem**. Étant donné un univers
`U = {0, ..., n-1}` et `m` sous-ensembles candidats, il faut sélectionner le plus petit
nombre de sous-ensembles dont l'union couvre `U`. Tous les sous-ensembles ont un coût
égal à 1. Ce problème est important en recherche opérationnelle et en informatique, notamment
pour des applications de localisation, de planification ou de sélection de capteurs.

Il est NP-difficile dans sa version générale. L'objectif du projet est donc de comparer
des algorithmes exacts et approchés sur des instances standards et sur des instances
aléatoires, selon la qualité des solutions, le temps d'exécution et la reproductibilité.

Notre groupe utilise comme algorithmes complémentaires :

- une énumération exhaustive par force brute ;
- un algorithme glouton déterministe ;
- un recuit simulé, algorithme aléatoire décrit dans ce rapport.

## 2. Cadre commun et protocole expérimental

### 2.1 Modèle de données

La représentation commune définit `n` éléments, `m` sous-ensembles et la densité
`density = Σ |S_j| / (n m)`. Les indices des sous-ensembles sont stockés en base zéro en
Python et convertis en base un dans les fichiers OR-Library et les solutions.

Les instances proviennent de quatre familles :

- `E` : cinq instances OR-Library de petite taille ;
- `CLR` : instances CLR ;
- `CYC` : instances cycliques OR-Library ;
- `STS` : instances Steiner de couverture triple.

Les valeurs connues sont distinguées par leur statut : `optimal` lorsqu'elles sont prouvées,
et `bks` lorsqu'elles représentent une meilleure solution connue.

### 2.2 Interface commune

Tous les algorithmes héritent de `Algorithm` et implémentent uniquement `solve(instance, ctx)`.
Le contexte fournit :

- un générateur aléatoire reproductible ;
- une limite de temps coopérative ;
- un dictionnaire de statistiques ;
- une mémoire de la meilleure solution trouvée.

Le chronométrage utilise `time.perf_counter()`. Après chaque exécution, la solution est
vérifiée indépendamment. Une solution valide ne doit contenir aucun indice invalide et doit
couvrir les `n` éléments. Le coût est le nombre d'indices distincts.

Chaque ligne de la campagne est exportée au format CSV avec l'instance, la famille, les
dimensions, l'algorithme, la graine, le statut, le coût, le temps, la référence et l'écart.
La commande expérimentale est structurée comme suit :

```bash
python3 -m setcover bench -a greedy -a sa E.1 STS27 -r 5 -t 5 -o results/campaign.csv
```

### 2.3 Plan d'expérience

Pour les méthodes aléatoires, chaque instance est exécutée plusieurs fois avec des graines
différentes. Les indicateurs reportés sont la moyenne et l'écart-type empirique de l'écart à
la référence et du temps. Les exécutions dont le statut est `timeout` ou `error` ne sont pas
traitées comme des solutions valides.

Les graphiques sont générés à partir du CSV par :

```bash
python3 -m setcover analyze results/campaign.csv -o results/analysis
```

Le résultat contient un tableau `summary.csv` et des graphiques SVG avec barres d'erreur
correspondant à l'écart-type des répétitions.

## 3. Algorithme 3 : recuit simulé

### 3.1 Principe

Le recuit simulé explore l'espace des solutions en modifiant une sélection courante. Il accepte
une amélioration systématiquement et une détérioration avec une probabilité
décroissante liée à la température :

`P(accepter) = exp(-ΔC / T)` pour `ΔC > 0`, où `T` est la température courante.

L'algorithme initialise une couverture avec la méthode gloutonne sur le gain actuel. Il retire
ensuite les sous-ensembles devenus redondants. À chaque itération, il applique une mutation :

1. retirer un sous-ensemble ;
2. ajouter un sous-ensemble absent ;
3. échanger un sous-ensemble contre un autre.

Après chaque mutation, une réparation ajoute les sous-ensembles nécessaires pour couvrir tous
les éléments. Une seconde phase retire les sous-ensembles redondants. La meilleure couverture
rencontrée est conservée indépendamment des mouvements ultérieurs.

Le coût de départ dépend du glouton. La température initiale vaut la moitié de ce coût,
avec une limite finale de `0.05` et un refroidissement multiplicatif de `0.995`. Tous les
choix utilisent `ctx.rng`, ce qui garantit la reproductibilité pour une graine donnée.

### 3.2 Temps et statistiques

Chaque déplacement appelle la limite de temps. Sur une instance faisable, les statistiques
CSV contiennent notamment le nombre d'itérations, le nombre de solutions acceptées et les
coûts initial/final. L'évolution du coût est une fonction d'énergie où une diminution signifie
une amélioration.

## 4. Résultats expérimentaux

Une campagne préliminaire de cinq répétitions a comparé le glouton et le recuit simulé sur
E.1, E.2, E.3, STS9, STS15 et STS27. Les résultats complets sont contenus dans
`results/greedy_sa.csv` et agrégés dans `results/analysis_greedy_sa/summary.csv`.

| Famille | Algorithme | Écart moyen | Écart-type | Temps moyen |
|---|---|---:|---:|---:|
| E | Glouton | 0 % | 0 % | 0.335 ms |
| E | Recuit simulé | 8 % | 10.14 % | 167.16 ms |
| STS | Glouton | 1.85 % | 2.71 % | 0.0349 ms |
| STS | Recuit simulé | 0 % | 0 % | 28.76 ms |

Sur les trois instances E testées, le glouton atteint toujours l'optimum. Le recuit simulé
trouve l'optimum sur E.2 et E.3 la majorité du temps, mais reste à 6 sous-ensembles sur les
cinq répétitions d'E.1. Cette instabilité explique l'écart-type élevé.

Sur les instances Steiner, le recuit simulé atteint l'optimum sur STS9, STS15 et STS27. Le
glouton atteint l'optimum sur STS9 et STS15, puis reste à 19 sous-ensembles sur STS27 contre
une référence de 18. Le recuit réduit donc le principal écart observé sur cette campagne.

Chaque répétition produit une solution faisable. Pour E.1, le recuit utilise environ 781
itérations par exécution ; pour STS27, il utilise environ 1047 itérations et passe
habituellement d'une couverture initiale de coût 19 à une couverture de coût 18.

## 5. Analyse

### 5.1 Qualité des solutions

La campagne montre que le recuit peut améliorer une solution initiale gloutonne, comme
pour STS27. Cependant, il ne garantit pas l'optimum : sa performance dépend du mouvement,
de la température, de la graine et du nombre d'itérations. Contrairement à la force brute,
aucun argument d'exhaustivité ne permet d'affirmer qu'il a trouvé l'optimum.

Le glouton reste extrêmement performant sur les instances testées. Son succès vient du gain
mesuré sur les éléments encore non couverts, plutôt que sur la taille initiale des
sous-ensembles. Il ne bénéficie toutefois d'aucune garantie forte sur toutes les instances ;
l'amélioration locale apportée par le recuit peut donc être utile sur les familles difficiles.

### 5.2 Temps d'exécution

Le glouton est deux à quatre ordres de grandeur plus rapide que le recuit sur ces mesures.
Son temps moyen est inférieur à 1 ms sur E et de 0.035 ms sur STS. Le recuit prend environ
167 ms sur E et 29 ms sur STS. Cette différence est principalement liée aux centaines ou
milliers d'itérations nécessaires pour refroidir la température.

Les temps sont mesurés sur une machine donnée en Python. Ils servent donc à comparer les
implémentations communes de ce projet, pas à établir une complexité industrielle absolue.

### 5.3 Analyse par famille

Les instances `E` sont structurées et suffisamment denses pour que le glouton trouve souvent
l'optimum. Le recuit ajoute une exploration locale mais une température mal calibrée peut
également bloquer dans une solution de coût 6.

Les instances `STS` sont plus petites au niveau des tailles testées. Leur structure triple
permet au recuit de partir d'une solution gloutonne proche de l'optimum et de réussir les
échanges nécessaires. Le recuit a été particulièrement efficace sur STS27.

### 5.4 Limites

Les résultats préliminaires ne couvrent pas encore toutes les familles CLR et CYC ni toutes
les instances STS. De plus, cinq répétitions donnent une estimation de variance utile mais
pas encore une analyse statistique exhaustive. Pour conclure davantage, il faudrait augmenter
le nombre de répétitions, tester plusieurs profils de température et étudier chaque type
d'instance avec un plan factoriel.

## 6. Recommandations expérimentales

Pour la version finale du rapport, les auteurs devraient :

1. exécuter le glouton, le recuit simulé et la force brute sur toutes les petites instances ;
2. utiliser au moins dix graines pour chaque méthode aléatoire ;
3. augmenter progressivement `n`, `m` et la densité sur les instances aléatoires ;
4. distinguer les références `optimal` et `bks` dans toutes les tables ;
5. conserver les CSV bruts afin que les moyennes et les barres d'erreur soient reproductibles ;
6. utiliser une limite de temps identique pour tous les algorithmes comparés.

## 7. Conclusion

Le cadre commun permet de comparer les algorithmes avec le même chargement d'instances, le
même chronomètre, le même vérificateur et le même export CSV. Le recuit simulé représente
une extension locale plus coûteuse que le glouton, mais capable d'améliorer sa solution sur
STS27. Sur les cas testés, le glouton reste supérieur en vitesse et très proche de l'optimum.

Cette campagne préliminaire confirme l'intérêt du compromis coût/qualité : le glouton est
adapté à une réponse rapide, tandis que le recuit peut être alloué davantage de temps pour
chercher une meilleure couverture.

## 8. Références

- D. S. Johnson, *Approximation Algorithms for Combinatorial Problems*, JCSS 9(3), 1974.
- V. Chvátal, *A Greedy Heuristic for the Set-Covering Problem*, Mathematics of Operations
  Research 4(3), 1979.
- S. Kirkpatrick, C. D. Gelatt, M. P. Vecchi, *Optimization by Simulated Annealing*, Science,
  220(4598), 1983.
- Beasley, J. E., données OR-Library pour le Set Covering Problem.
- Kritter et al., *On the optimal placement of cameras for surveillance and the underlying
  set cover problem*, Applied Soft Computing 74, 2019.
