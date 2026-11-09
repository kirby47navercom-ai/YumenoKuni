"""Compile authored loop thoughts independently of noise staging."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def build(followup=None):
    if followup is None:
        followup = json.loads((ROOT/'data/presentation/nonstop_followup.json').read_text(encoding='utf-8'))['tasks']
    header = '#pragma once\n#include <string>\n#include <vector>\n#include <stdexcept>\n// Own authored non-answer loop monologues. Generated from nonstop_followup.json.\nnamespace nonstopv4 {\nstruct Hint {const char *task,*text;};\ninline constexpr Hint HINTS[]{\n'
    for task, row in followup.items():
        header += '{'+json.dumps(task)+','+json.dumps(row['hint'],ensure_ascii=False)+'},\n'
    header += '''};
inline const char* hint(const std::string& task){for(const auto& row:HINTS)if(task==row.task)return row.text;throw std::runtime_error("Missing authored Nonstop loop monologue: "+task);}
inline std::vector<std::string> thoughts(const std::string& task){
 const std::string text=hint(task);std::vector<std::string> rows;size_t start=0;
 for(size_t i=0;i+1<text.size();++i)if((text[i]=='.'||text[i]=='?'||text[i]=='!')&&text[i+1]==' '){rows.push_back(text.substr(start,i-start+1));start=i+2;}
 if(start<text.size())rows.push_back(text.substr(start));return rows;
}
}
'''
    (ROOT/'Game/Source/NonstopLoopHintsV4.hpp').write_text(header,encoding='utf-8')
    return len(followup)

if __name__ == '__main__':
    print('NONSTOP_LOOP_THOUGHTS', build())
