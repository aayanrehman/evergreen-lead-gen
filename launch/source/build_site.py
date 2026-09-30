import re, subprocess, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "site"))
def dims(p):
    o = subprocess.run(["sips","-g","pixelWidth","-g","pixelHeight",p],capture_output=True,text=True).stdout
    return int(re.search(r"pixelWidth: (\d+)",o).group(1)), int(re.search(r"pixelHeight: (\d+)",o).group(1))
def img(src, alt, z=True, cls="", lazy=True):
    w,h = dims(src)
    return f'<img src="{src}" alt="{alt}" width="{w}" height="{h}"{"" if lazy else ""}{" data-z" if z else ""}{f" class={cls}" if cls else ""}>'
def strip(ids, cap):
    return '<div class="strip" tabindex="0" role="region" aria-label="%s">'%cap + "".join(img(f"img/{i}.jpg", f"{cap}, slide {n+1}") for n,i in enumerate(ids)) + "</div>"
A = [f"cA-{i}" for i in range(1,7)] + ["s3-impossible"]
B = [f"cB-{i}" for i in range(1,7)]; C = [f"cC-{i}" for i in range(1,7)]
S = [("s2-andrea-blank","Authority and guide"),("s4-deadline","Deadline"),("s1-start-here","Start here"),("s8-cartoon","Cartoon hook"),("s7-testimonial","Real review"),("s5-draft-story","Consultation"),("s6-what-next","Consultation")]
statics = "".join(f'<figure>{img(f"img/{f}.jpg", t)}<figcaption>{t}</figcaption></figure>' for f,t in S)
libs = [("891868123359632","thecollegeappqueen",78),("1042251592179459","Admissions Narrative",17),("2084754159095048","Collegewise",27)]
libh = "".join(f'<figure>{img(f"img/lib-{i}.jpg", p+" ad")}<figcaption><b>{p}</b> ran {d} days</figcaption></figure>' for i,p,d in libs)
shots = [("home","Homepage","Consultation form above the fold"),("guide","Free guide page","The offer the cold ads promise")]
shoth = "".join(f'<figure class="shot"><div class="bar"><i></i><i></i><i></i></div>{img(f"shots/{f}.jpg", t)}<figcaption><b>{t}</b> {c}</figcaption></figure>' for f,t,c in shots)
hero_stack = "".join(img(f"img/{f}.jpg", a, z=False, cls=c, lazy=False) for f,a,c in [("cC-1","Ad: 4.0 GPA, 12 activities, still forgettable?","h1"),("s2-andrea-blank","Ad: The college essay is still blank?","h2"),("cB-1","Ad: Another college checklist won't tell you what's weak","h3")])
T = open("../template.html").read()
for k,v in {"%%A%%":strip(A,"Carousel A, the blank essay"),"%%B%%":strip(B,"Carousel B, the first thing to fix"),"%%C%%":strip(C,"Carousel C, strong on paper"),"%%STATICS%%":statics,"%%LIBS%%":libh,"%%SHOTS%%":shoth,"%%HERO%%":hero_stack,"%%WS%%":img("img/workshop-ad.jpg","Sample ad: free parent workshop, how to help your 10th grader find their essay story",z=False,cls="ad",lazy=False),"%%PH1%%":img("andrea/andrea-speaking.jpg","Andrea Schiralli keynoting in China"),"%%PH2%%":img("andrea/andrea-workshop.jpg","Andrea leading a student workshop in China")}.items():
    T = T.replace(k,v)
open("index.html","w").write(T)
print("built", len(T))
