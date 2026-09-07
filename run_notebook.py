"""Execute the walkthrough without a Jupyter installation and save text outputs."""
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path

def main():
    path=Path(__file__).resolve().parent/'analysis.ipynb'
    nb=json.loads(path.read_text(encoding='utf-8'))
    namespace={'display':print,'__name__':'__notebook__'}
    count=0
    for cell in nb['cells']:
        source=''.join(cell['source'])
        cell['id']=hashlib.sha256(source.encode()).hexdigest()[:12]
        if cell['cell_type']!='code': continue
        count+=1
        output=io.StringIO()
        tree=ast.parse(source)
        expression=tree.body.pop() if tree.body and isinstance(tree.body[-1],ast.Expr) else None
        with contextlib.redirect_stdout(output):
            exec(compile(tree,str(path),'exec'),namespace)
            if expression is not None:
                value=eval(compile(ast.Expression(expression.value),str(path),'eval'),namespace)
                if value is not None: print(value)
        cell['execution_count']=count
        cell['outputs']=[{'output_type':'stream','name':'stdout','text':output.getvalue().splitlines(True)}] if output.getvalue() else []
    path.write_text(json.dumps(nb,indent=2),encoding='utf-8')
    print(f'Executed {count} notebook code cells and saved outputs.')

if __name__=='__main__': main()
