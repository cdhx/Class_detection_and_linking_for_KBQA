# Class_detection_and_linking_for_KBQA
A class linking tool for KBQA system, detect and linking class(type) to DBpedia ontology

## Performance
Experiment had been done on LC-QuAD, which have 5000 complex question and 1990 has a type relation(aka. rdf:type)

**Linking performance:**
|Metrics|Performance|
| ------------- | ------------- |
|Precision| 0.519971|	
|Recall| 0.76411|	
|F1-score| 0.580222|	
|Hit@1| 0.691027|	
|Hit@2| 0.743849|
    
## Notice that 
The input of this program is a EDG structure, which is what our EDG team working with.

In the main function we give an example of EDG, input this and output the linking result.

## Future work
This work can only recieve EDG as input, we will make a version that recieve question as input.

Another work is to expend search space to the whole DBpedia, which has around 800 class(LC-QuAD has 187 class).
