# import the json utility package since we will be working with a JSON object
import json
# import the AWS SDK (for Python the package name is boto3)
import boto3
# import two packages to help us with dates and date formatting
from time import gmtime, strftime


class Node:
    def __init__(self,data=1):
        
        self.parent = None
        self.children = []
        self.data = data

class Leaf:
    def __init__(self,data=""):
        
        self.parent = None
        self.data = data

def build_tree(molec):
    """
        Takes in input a string, return 2 trees: root_node - which is the tree of the expression molec - and curr_node - which is equal to root_node iif the expression is well-formed.
        Build the representation tree of the molecule string, where the nodes contain the number of occurence of the child tree, and the leaves contain atoms.
    """
    curr_node = Node()
    root_node = curr_node
    
    i = 0
    j = 0
    while i+j<len(molec):
        if molec[i+j] in "([{":
            # Add the child
            child = Node()
            child.parent = curr_node
            curr_node.children.append(child)
            
            # Update curr_node
            curr_node = child
            
            # Update the indice
            i = i+j+1
            j = 0
            
        elif molec[i+j] in "}])":
            # Update the indice
            i = i+j+1
            j = 0
            
            # Extract the nb of occurence
            if i+j<len(molec) and molec[i+j] in "0123456789":
                j += 1
                while i+j<len(molec) and molec[i+j] in "0123456789":
                    j += 1
                nb = int(molec[i:i+j])
            else:
                nb = 1
            
            # Update the indice
            i = i+j
            j = 0
            
            # Update the node data
            curr_node.data = nb
            
            # Update curr_node
            if curr_node.parent != None:
                curr_node = curr_node.parent
            else:
                return root_node, None
        
        elif molec[i+j] in "AZERTYUIOPQSDFGHJKLMWXCVBN":
            # Extract the atom name
            j += 1
            while i+j<len(molec) and molec[i+j] in "azertyuiopqsdfghjklmwxcvbn":
                j += 1
            atom = molec[i:i+j]
            
            # Update the indice
            i = i+j
            j = 0
            
            # Extract the nb of occurence
            if i+j<len(molec) and molec[i+j] in "0123456789":
                j += 1
                while i+j<len(molec) and molec[i+j] in "0123456789":
                    j += 1
                nb = int(molec[i:i+j])
            else:
                nb = 1
            
            # Update the indice
            i = i+j
            j = 0
            
            # Add the child
            leaf = Leaf(atom)
            child = Node(nb)
            leaf.parent = child
            child.parent = curr_node
            child.children.append(leaf)
            curr_node.children.append(child)
        
        else:
            # unrecognized configuration
            return root_node, None
            
    return root_node, curr_node


def count_atoms(molec):
    """
        Takes in argument a string, returns a dictionnary of type {"atom": nbOfThisAtom} and error, a string, empty if there were no error.
    """
    error = ""
    
    # Security
    if len(molec)>1e5:
        error = "Molecule too long"
        return None, error
    
    # Build the tree
    root_node, curr_node = build_tree(molec)
    
    # Check that molec is a well-formed molecule
    if root_node != curr_node:
        error = "Malformed expression"
        return None, error
    
    # Count the atoms
    atoms = dict()
    counter = 1
    ind = []
    
    # Parkour 
    contin = True
    while contin:
        if type(curr_node) == Node:
            if len(curr_node.children) != 0:
                counter *= curr_node.data
                curr_node = curr_node.children[0]
                ind.append(0)
            else:
                # Update curr_node
                curr_node = curr_node.parent

                contin = False
                for i in range(len(ind)-1,-1,-1):
                    if ind[i]+1 < len(curr_node.children):
                        ind = ind[:i+1]
                        ind[-1] += 1
                        curr_node = curr_node.children[ind[-1]]

                        contin = True
                        break
                    else:
                        if curr_node.data > 0:
                            counter = counter // curr_node.data
                        else:
                            counter = 1
                            loc_node = curr_node
                            while loc_node.parent != None:
                                loc_node = loc_node.parent
                                counter *= loc_node.data
                        curr_node = curr_node.parent
        elif type(curr_node) == Leaf:
            # Update the dictionnary
            if curr_node.data in atoms.keys():
                atoms[curr_node.data] += counter
            else:
                atoms[curr_node.data] = counter
            
            # Update curr_node
            curr_node = curr_node.parent
            
            contin = False
            for i in range(len(ind)-1,-1,-1):
                if ind[i]+1 < len(curr_node.children):
                    ind = ind[:i+1]
                    ind[-1] += 1
                    curr_node = curr_node.children[ind[-1]]
                    
                    contin = True
                    break
                else:
                    if curr_node.data > 0:
                        counter = counter // curr_node.data
                    else:
                        counter = 1
                        loc_node = curr_node
                        while loc_node.parent != None:
                            loc_node = loc_node.parent
                            counter *= loc_node.data
                    curr_node = curr_node.parent
        else:
            contin = False
            error = "Malformed expression"
    
    return atoms, error

def toString(d):
    """
        Converts an atom dictionnary to a string, sorting the atoms by decreasing number, and by alphabetical order if equality
    """
    # Sort by decreasing number, and alphabetical number if equality
    it = list(d.items())
    it.sort(key=lambda a: (-a[1],a[0]))
    
    rst = ""
    for cpl in it:
        rst += cpl[0] + "," + str(cpl[1]) + ";"
    return rst[:-1]

# create a DynamoDB object using the AWS SDK
dynamodb = boto3.resource('dynamodb')
# use the DynamoDB object to select our table
table = dynamodb.Table('AtomDatabase')
# store the current time in a human readable format in a variable
now = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

# define the handler function that the Lambda service will use as an entry point
def lambda_handler(event, context):
    # EXTRACTION: extract values from the event object we got from the Lambda service and store in a variable
    molec = event['molecule']
    
    # HANDLING
    atoms, error = count_atoms(molec)
    if atoms != None:
        atoms_str = toString(atoms)
    else:
        atoms_str = ", "
    
    if atoms_str == "":
        atoms_str = ", "
    
    # DATABASE: write the query and the response to the DynamoDB tableand save response in a variable, not yet implemented
    #response = table.put_item(
    #    Item={
    #        'ID': molec,
    #        'Time': now,
    #        'Atoms': atoms_str
    #        })
    
    # RETURN: return a properly formatted JSON object
    if len(error) == 0:
        return {
            'statusCode': 200,
            'body': json.dumps(atoms_str)
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps(error+', ')
        }