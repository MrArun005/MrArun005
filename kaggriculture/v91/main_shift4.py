"""v9.1 counter-fit: v22 route with all SELLs shifted 4 turns earlier.

The production route is a real fit-only trajectory.  Runtime adaptation is
limited to identity-free weed recovery and in-place ranking of existing SELL
slots by the official 1.32.4 price-impact curve.  Ordinary turns never create,
delete, or resize a market order.
"""
import base64
import copy
import json
import math
import zlib


_ACTIONS = json.loads(zlib.decompress(base64.b85decode(
    (
    'c-rk<!ERhha{QHn&U;WdyD7>yj@0WBmLm-)X^HiK7!2Sw3>fRf*f+!fZpjqculq%2L}cY_QZu?yBD-HzR#v^r$jHc_|L57i{rcNK'
    '{{GvufBNp{XFpxOfB)?EPv1TJ_h0|>U;pd#e|`SPKYsn~KmPvTpa1pqvmf4E?>_&9{?qp#|Mtt}+c!U6UOoHtUGIO`?SA_7!y5eV'
    ')w`R6-'
    '@M=LUVr}on;&+UA3pu?V)mOKcUSM;e)?gxzP<h5KYe#Nmp8Be^6{s`@7>Sq=Vv#&_aE*?`1alPhac{Kyf?t~<A+1O``EErJ`d`r>'
    'vyj|zWOj7F&NhOAKzTP{^iqiK772h&~!|bk&r>{pD_93!%@vGa&`G?cW)5$$@AZnhuxcZ`jFY&gNMa`M;@9Qcfa7D4DoidPRB;RH'
    '`Cq1HyQZhnRh;W=S!C#cGt&`|MO?xJ{;zkj}$CEdBSA+56^mad2in@f7oo_$z1mj-TxihOVYH^0zzW~PdffAU(=&U8TLi4q*?mmi'
    'z^o1yU@6WnY->?$aL5F6AZ&ne5lo&(Sb0xg<{zG>(nsp^gm6@g2y)76V5C(82IgU^OnsC?Ufo)-'
    '1qqm!B5RLL_dXg?VrrCHTx%X^wVQM;Qk<s@4mq$?<~7}?*FLp&EWcYf3$ae*Zkan8sjRj1o*Cp`{nO>lDo^kh3p*Ht9MsdyH_86`'
    'Sb4j!<(x&|8o2amcRM)CVs!W`u`|#@@4R$@85mwTk*CT%)a^c^}C;*;zlm}l5`BNn!fqTZfm|2svmo<=Wl~yU%#Koer*K@Sht`{p'
    '`%O>iey~CeJCIVApq%VbN@Pc#3X`pA10mOhYy2`Jio?@J75JZF71nhVZoRL-J-`wf>vX4+eNFfj7i2<$}-'
    'S;WT~X^v3($U&_3=nZ6<-C=Qo>Ni^tl+MoHq^?vc!IPk|-'
    '&Kiz%gBm?<FTZCP2L`38i_Q?lgn&;6C(FWx_{uANdeY4c_zV@%3UH&%<q?UmLY{J~KcsZ9-'
    '!}s4RL)hfb2Ol>ZjeHSxZ{d~4w;1#&Z>l~DS#yTMFJ?>}M3Rg0@vrNTM|MW@ggN|<*lMMPH2IjS23e~^%HOZ#CbG<s@|9DPOx+{O'
    '*RAt9AVV~xx0K@LK^`B#*B*OFPu*mYXYkEp?ki@YAw3=AES~#)+-ENxMErqr_Dy;Al@)c+_+y(eSbO7-'
    '!x#Nx5eOrHj$a%rfytib)|;Bi(bRo@pu-er+FeY;nokiTB9lz$h7$3KWMBwUb&!8O6f+J(UzOa-{?|WTUjNmZ{+S4s-'
    '^WOF{w9a+VZ71fFyJtA_Cew^n$u)xDoYkw?%-'
    '=8Y$Kv7lLz9<ANabxJ>|GsOra1X&iuybBuxJE;79lnWg>av15=oTOsh!a%n9NTk3Mh}G`(<l&tDo2ABwGP&V3HE(B4UaR^@ODqJ^'
    '3GLvZrW5-i);Hnk83SO>c4J)i60*A+kA8v#CJW|=`o58r&z@@vnpX8=U-9wG7b-B$*z%kXpIg?0C3g`uJ)DhynTw-'
    'P*}F!CZTTl`=Q{1%3aa<0-'
    ')3#(H%a#nvP%^(3ahmV?qC1SvEcr=6fMbig^H`Vs`^h0U<;A4O?!Izvb1h||n2(z3vy?bYlcIX5?3%%o(;Ze4d^M**S#3Y*eeHv?'
    '0t9cT@D#g%T8emJrKT4Y_FfZ}qE;~(Yja7h%0D#_lo)xGR>K?Z7E|o9q#&20XJ2qsM64=4StlZhq=v$&$h904B4ltFmNV#UI$yxg'
    'D-PN6FNr+XPkI-9kU%BbANB$7i?r8YD@L|Y7=a;!{TTRl{<=fX))f+8j2BJ369S`4ejLY-OSswHKhwICm?|0YNfBW>W3+*aEL|@W'
    'e=3w$sRk}DLA5LBhsR&R>7biv+!Y`g2(%cxu3o}@y$z#!PA4a;*%^m&ODX!P)>c#3S8McWpip48AOs&l_*FlzTvfUP3XIP4euQDA'
    'q5bE_0S`MZT_m*p@9NCBzQnW@#<I4BcY*yXFHX_7W@#^@vR$S8>_*V1V{lf2mn(+>VoTSOg+YWjIEG)%GJG=yw8V6yx#0!vJ@%v_'
    'E={F-wKN-X1(ivGCPQ!DBtvp&ieV8}~{&5m-c-J0z^e~=E?;3~pos7^rz)FV1dqy$uEO4t2Gbb?5v(+t})a@8Em&C0lvg-MOX*!g'
    'ejOph!ujYdZ9oq?97bd#axU5`o^&kM;xH0SD>maycI1;DB`JvTw?Hx1`<%F6x(QFDoipRpmtwAe@AG)6yyjpjR^ragq;fL;L!v3<'
    '%hP9mmXtmDXM7#L~3y!sO)VU|XC=WRT8eI8Sg~rL0ancAqP#=vK01|DNb`f@i76^#SQds%S=anl3#Rdp;mCT^o(*w@s^nSLZaYV#'
    'U>@+&em4Gt^a}PuQWT>w?Qn(4;HvzpHI?D70m=aE9;&%P|oHKT#&4>@}MCB&T`46N4p$`*^0jq8(bL>@auy&L~7eK#m$)ZxVU|cC'
    'sACHsiLc2AfkIPEv0lah{-~IUJ>MuC5Ljw<@@pM#j(LLqCGsgR<sTmi2H2>?_x-u>@SS`b`O6m+&il8YSQL>w&q2E2FR(I4t8Yy-'
    '!7=|MWdHTJGDQs_-'
    'Z2c0ocR9cmUQ{uKwS_6HIxvO1pGK&kP)KMTNtl0c;q89hL?R4fec)g$TYg*%DkO#a2bSlkP;TuZL9GKBVGeHcjYBI7uaj0Z%BE1R'
    'xIn9%uY8sSOhdhL9STB96zjo)Ukkse!_{mYG>p%^pne&Ko`hChNxkd5iXw|lPp+E|;U%{Si9qsVTmzWlsn&JAU|hmfg#e|z&zmwb'
    'IfSh<x)$zXBDtdAqRM^K$tQl{z;0wz2^Z#MO>!1pevX&QYrK>*G$@p{k13CZ9%V?~GFN?jgjV(s>#6<jjrld$tgTs;FJk2;<kax`'
    'EcpMe8EZ$m6u+AS;&g`ze3-pknukuV;QKMLl>R~zU8+<TN!hm$`$sB6cPSxz|7-Mrw7O!nmQvP-'
    '+M5<R#!1=R<jlY@3~~*i$yCYstyF?^?jAwj2X4vnoV?8HW<fo+JYq~F;eR)08eT=&NZBb|_UyAhelK+w1YiUoa{YWW!dS;1L);v~'
    'g&n;0^V^{cM10)A(*~1tP5!bt1!Jp{ynb*-4h;LQgY2vbH4e)i1uy&~VwfR1OP$z}!-'
    '~P{WikYKvm)4LB0Ylaee}O~nc%bA0eLVy6H2!@{wYjW<AFc?Z(-'
    'wdRu+aNC#PyKJt;eEs1R~kp9rLBKCYb{&?lXRo=Mb2CY!JG+4GnS@KSu=qapE>xBLJ5N!D{D`AA!n@T>?Ye}rFg@FX|^dYSw^M_}'
    '^0(lEuK=75)*M}L7&$+0?%1Lnh8YM{Fj3KI^^h;uqxKrT_GM@uk7jjpiFJO%y9rGr?6;2V#FU>p=drUmW<50EF14OX80P>V@ad;u'
    '4Stv3mTt8*>_Ca5|?aB4GM%vq4o09h4tH@+d`xJGF;7978~*WJ5CHz&Olx{-'
    '`r7@zNlT%^M)F=3%x&aasm6clWK`R$Nx>{kXlDTNhQig(auk)5m!@a&lkq@*Zkew0kNhVC8c<5r<oF8OX^OD{xV2IA;a1&~$8z|7'
    'n$TJS<-$2&ADZ+ox`8R3<bA!a2o#%#w!>s)Mc2NK{#0Ex#D?6FWA>VxkSq;+{-x&#jzi*85jV*+cvQ2oiNn-caOnsJf(#Hva3(ly'
    '&k8U#9@YZwJN+fXK6c^uMwWh|s#F<YtYhp;y^rB2Gdn;1bz66EDQiJkmJqp*;poI=7>jS;>2w4+MgffrYSsW`Fo1cfagWrG&6G-'
    '71;&(&nuA(NPomJ0G*(qVnxbGNvVb%H5w2D#F1L82i{Ar<_4sk!6})AN(5!1UyWiHcQ%+rcaVA`cEI?5;L-'
    '#TgZ#T#T@YAj`?1ump-%iMa$d4ZV{g2O#4gouY>VS#-n&tnw3Oluh*m0lH2^kWQh5%2VhplX9GYI7RL!S83uLv<66NGbSEn-'
    '$|9_X#(OmBQ#x3Qq0+;c}K;@P9;QrtU*9kuj(SIV<?hBEmwyQjFqhrl+xOLS*B8JR+`!2fftsQvfJ;X>+6J;Kq4WG?hf^j*uRBR&'
    'JKhg$tL8el^cqyL!^6AMTUl3olvJ|nejW0>BRsO(y?Yh`&751Zdk-as?oP}3|kuO>N!65Hj8*K6C_f%wr|d3>L1aaTco39F(wyVO'
    ')tvMD~8l(<&b(MHdk!a;VA{uCGJ;;CMzq#=vLMtp)tykH;qPJD;Sfp&IN?QSYIjdT4C#C-'
    '>%ek3dBc{Tg6$4p;gl5WYXKFZW>7AVC0SbKNAX1o8BZFSA`~Iw<pZUz&fk!Jh>maF%n_-'
    '^_Yf;q+sWSIRt1N(iUStUo)#+lXREM2M%L0(G8s%wX$A2RrL!lTzWQlD!&kNV7IOoD{ay{X(jEo8k<PUGHxio92%R&%Zb|wXVF?='
    'n6r5JWs>5Bm7C{dRm_m|qxV}Nm~7*kI0~utDn3`_IS8L~^2dR1*J8?+HmI8g61QT`a|wypwWvYUqThOy+&PY!mQspgJzW|azKcpQ'
    'OswHJT02DoRm$2G`m~E#F+E8Xi@BU46H4l+T32o}uyXiPXRV#A{DGw#(rnp`L(r{=0YkbxY%Dhs+>DgnXjj>$@{V)Agp5QCmPc(z'
    'h~N-'
    'qLm`9ZQ0KO+6vtznbvnPbdzmox1#3yp2lNOMt*sh)`|ei0_Dz!KDP3kmFe<0NgRGQ*#@i$UERc5ON*K*a1bq+q*34x!j`TA$kFlD'
    'hx{(g~XbFksri0w^GHNF1-'
    '^e9sj~YFF<(ars<m8O>T$QsMOra}}hw~v$BM3LI)s*r({lJ^DgH)7~t<&Qq5}m{u$(8i_2^#{rR=EiDiIS7fy_kWZC(dK$cQCeuy'
    'Z6Ja#8SSqPl4jJsZlanctbRzV9tzdORJVvfYfy^k%W!a3xz|5sS8S8&zn=Q)FUOUkd$DSi1uBmn9Qu@gEQvaA%CwW?@5kGxD`pMA'
    'gdI0#~tO1^6`3Q+-'
    'w1&j>5<DA5QkNJzZ)(1eXC3LCf7CNRB$77t1|)eKE%>KiTB=LcehY#N>(lol(9VXsdOa9`DbD3kZYN=y<>wzCbhgFDMY3mpYGdpc'
    '^|TkIJNuQn|m9s%cPhaXyxf7rLqFAKf&yhuPe=CiT}+Y4hp&!!X3+uvPfObPkTkZ9MIRzdL(8_5i}3&=s+{I@?ZB=fZIjOe-'
    '^u$CKH)H$h+z%}J$=oA%ziE)t#9`IsO6dLGa}{Gxjvx!<t<6b!sFOLE2SSucB{oh`JAjiJQ*nd|)#iU9+`BOf~WtnWr!yK)=VEW-'
    'FHSM{7$JW5~<4^!!nOrp1;?~q-`9g&I&Y5T|v@NX*UX<U*j09^x&e+G!=0CS-WmRkc6LXEH;TD(VjqIaOe8we5x1@<MW0I^oW!Sf'
    'i@s1Vx$5aL^uhOPl(8xR5y9AN&@N{d=`MHOLNIO?1)GKp+Lz(cR*W_^U<Q7D5T1@jWxlVH?L!E|`bIIJVAH7Qn&e2wMbn|9L4`fD'
    'Ja&>sV(+=WRcVHB_NG8SVBfZGCLXrxw6rn*{`OhRsnj8M=^8%e0LSz}eks6Q=9gg1lJgT*>0M1K#mu9E_=&`bbHn?uIkDBO%a3|Y'
    'jI<8VAm2T8Noyig_q|I;ct^{>I_c5#m0<F{(y!kr|Cxaej5pzI<5=ve7}@TTommSWz5=M*J}>)xFoyNry1Z#d2>NgXzkQ}7s`9iq'
    '|%l!mhRo^jBA??OzDSv&__nI>|YTtU9x@6-'
    'cviDabAF{~UgwVb`xELEL}TD*VQ*HP5DL$^Nbg$^cx(q&Gs7&xIscK$`%CZdwA{0bhvP~bt+$`o?C@>ZL2)aXJgMua>^S`&*b^W>'
    '=%LzOtAN(CpWzEKBxRwO}a8TvtXM~6y+#)nwTya`sC)U8>pmiAW=7=~{OwmPwF0LTpGDJy-'
    'p<)v&QY`~BYl2G)BF}?Pkmflfdp*Ud{)B9SQ^?^JSXYN&PtSq$X?wo1WARB}bD`t+9eQtjPx5yoy2PAt%uI))$zdj8Z^5riBTI&`'
    '^;-'
    'p+*nMHxVL*!1eZ=&p6$ocV(#6pKUe%)pWG%r)A>x=929F?`iC&tlgz;garvz|hPNQgnNq(FPVqEn%%ASMmW1R6mXu9f2ttg?!%np'
    '6ZL0=w|})zwkhf#rynFeF&kiWHmTPSm#X4-g@pdJ=fB*R<ET0=6y!M=_Y%wWCQ{bf<8MobIvKHIFZ&K;R*Dx&>c#MW9GW)4but{-'
    '*}t>+L)tow0{Mb)9722un|ru#|r61jt-K{xAe{N=3sRV9m-^VL%5%4r{Qt_HLoNC%Xe-v_VS5sr>EUjGk^<8k`=Lf57Uyh~0Dw<Z'
    'W}?LD~xIob#n+sx;L|a|j=nJE}$m8UbibFvlUE^>Gm<qHEI@o2qw)1aD;~LWF%3m$0MS?i}F@svNqZ%)@L1|8g9MOhSwc8DGu`n<'
    '^hqS#g<=R0l5e?vz&foK=b=6^+Siy3?ggh#*0YiYH%1)l>+&!9PE~&~O{88A=Q2kj^mX0s*j}5}1^Fqm{VK7O=?P#)589^#3`ZSG'
    '|4&&aIgOA`l8gHz^t8thFlI--t^<#8+6$$Tq1^Rg8?aF-mBj0xlD4MWs(9IF1V|hIn3yNTJIdR+YGdDXq@=c4I}5mNs=!dCii##%'
    '|J%5$bv8ou*7x;PWwj@XMbwGP?sB=W~et@yTm9om>=r{g`lPN-'
    '3lDj^`Fjk5M4OSL@*Ls%)*nw^c4nWUx1R&E;7a4Rne2M!C#3l5r}a<|mu9*zN`q14BMMgz_Z8lhG#G<CB*?A9Vl|`b(mZLB*3;0C'
    'Nc0eBnAdys{xLmzv&io%-r@H?AYcEFcb12l2wu_gFO<vU0l9r-'
    '<L`C}D4>N@O$Wu%vB2+LVg;F#|zK(H2=f03Ox(Z@NA{=CE?T^Z0X83@yunB`MM&L2F%0URiK7om^0h7j2t*Vyya>#9_L60^PgE<E'
    ')hSo8`E|Y94)9x>lsh_=Orhr6>@&O)_z%nMR+y0g(t~xNiX7?D$)jHL-BptwCHyQR&RIO$4{Q(UnjTt~|Ir<P>9TBJuG9fT=7h$6'
    ';%o?WlF(kR~)UV4-?Bxs5vN5OJ_1vO5I;(f<U)n{&;%hwAMx|A&LL_462>-'
    'MU?EdBs4k9YpEdL1ZwdaaVL51XIR`SB}s+;HfQ<n6Ft*sYT)hb$xyZEgoCbC)x3F^L2u|2uc~Ow_Zz0s!E~q0<9rg6}?XU)c&)-'
    'FC+q#sBR7I>JusYE!rs(%CH;iYRu=BY844RM<G7xLzlFhbML|THRL{y$=Su7)xlYu9l{kotgOV4BV7pre^xOH!U_!*MBtb040*Ze'
    'Ph97!RgqeZz@UNvi!3PB=0ybr12Q19mRK|NkA_ZKe4a!N6XXSoAtR?9Oc0vjdJm237xh+?x*jMMEzSX<$Xtx6#4#NN0UQuch*a#)'
    '3R{2NUA=p2P&d)B)2OmYIb)@nAITX?C9U3DiWOTCR@?Zj&Q@?)*ZPiBD!1hdEPcK%%8S+tMb5B$sw!eALv^Bh!jN_&mpY6EFjc)q'
    'jwBRr>8J=exObpGolKDYXY%Vp2{`9cmKIdf8R1wBM8zC3P7>q{t+604$<ZvC{VVsIsEItfbXG55*iS>e&gF2SHdB|KnbvrGwbaeC'
    'uLRv&xrDNmfJl0gcJnZ|%>ba-#UuUYQ{`%Iduow$Qx?gZrf+t0R)-'
    '3e#mjY#tLaxqsT9T$v=dq+yvvi~(ZC~8`pgMkKV@Ua{4b`6M_Qb?EHE_di`#lL7HxP|mO+Omm*O)L{Z`fyAx6HO&J=^Pk~*i6q$$'
    'FHo5?oj9Z;(-{6ef6W2WZ9Hnj1DPIw&U8taScAXm~Nryx^x5if4t#-'
    '@}ZCx`{G9}||XL^)PNIYZ!?*2qhxAMQ>aV%F+MrpUKaGl(MEuH_pqZU^XsR{xxE>%kW)=RlD}N>-'
    'W%^9qFH&IKJDC0Vis!6qNBy_F6`p`MngNVDrvmSQvar%L&vuZ=7R$jw0TGMxf|GeUOLXUYjN``AQ@v)FZr8OYAPH^bR;+_?v&%Pt'
    'Z^==082KUT9{i{+SKMFNdldQRvty3Bc%PiDC<eFn#(xz^KF?y?GtNiU*Sd+3&#FDr2xLCV|HL&{&D_^D0?9fXTJU|^_t%Fw$Mxhx'
    'fAcW^^d`898*I$BEJ;YWFw8HJ70GV($*a7Bxhz%!+8IRk7^dPPFmS+oXujXGnS4A4L^k65|%@yLdhuX?xvp@lLhCVSo@>c;ab1R;'
    'DYN(@NGSk7XMA*!_GD{ybVe)G@C&6Y}}!5N!TVXoL<b=N>nVM-};-'
    'UN#eeUD=*3<T+@ty2Bf{opfXYn#Mr9nTS!29Y9ET)&!+lQYY>Ysul|A|yE`*gHQG6az%(V#Z~xbWl=3K>`0GhM-'
    'm9ZcIvuP@0C}%Nm-*+8x*quU2T5`{NL_(h!p*tj`5It1vodndFYxyQ4jQV7u*?mO3ViH8>mzml6t{MyG5;=Vz0QN_1F-'
    'nxNA(w1yY;hl5?X*-'
    'Y5c;D$&YwPR&wuWwIYxd$X$fsQ7O9(o!D&GyFLc}Lv<Cfa1b+%_>Y*Sxd%qbX#fD%2V?bNw{MBJB<^q^W8r>#}3kazkykt;9{C{E'
    '0QT6!%bf7wQ{!zl6x2UMo+!koUHXkvmr9+L(D4Zo<`LmF!yAmG*|*DFS2nLigBs`Nj#;q&nfy(Zi(FI<p&y^_e1Lc-'
    '6upC1}17Ld&g`MmnXqMYxa~C6p$yjjBsV735OKx(hy+p#rkU-FDxRkC4<&TxwZo-WD`A!%{pPf8R$%M)xmyFKAv&0yAM@d{SE(Z!'
    'bXPWON}tk!4|^{27}FnREvcPM8{juj%=vr_$2Tk5md5xX3XHiApELb)p>4E-'
    '4LUHChgCD0p{~t;YVdqV@?$e|{EBkW$F2@@*w{DhcYyN~|@pjE7TO6QdPgyK?s>apkpy#9H8b?r$WhXQg};<n=nfr0I>2@i4Q-'
    'v;QP4{*{HV!#s&n*2TBL(Pxn_<rD!~6n2aOUvHlUbxt^Bk1Qc~=z5afpU$6-guvNp`JO4ou}f7T#Vsq-'
    'T?&4#m2;nh2@0WMgsl~sprYW*5U-B_1H+t9Ex|oR4wXHLkJjwHX$QtlnFz{R0^vTnC--_4qdo9)k3813ic}d+d34tq>e`c+>GLE!'
    '17#8jtgwd&z)klMyS7Kmym!yMoq^r71x^F)AcgBk`iAD4$V6Ch>HSV;l}dWZ4|XTIj(X*HWm^0&^~$0=7A-'
    '1!N)TUK{yT`_`?cFvD`F4}VUKV{igAha&LElsXS{KE>N}yxk*^*klZ|zQVW*-'
    'Lt2+izXYGMq{LIm4()oX4_AWlhQ~sGxLe48vg_6yp{4G;(zS(Il(VIG-'
    '<MA>gC}FEg+&T@p+aNUVYzVMrgjY)e9)80p%XN(*NT<n=;|+qdTT!1cLOa%;9Q0Ig?w(^5jG#i6)~Puyf^JeFUUCKMok@>M>3U(d'
    '>>mVUq-f(}WZ2(}GU-ZUN<Mk|YejUlHt7rr8k+N2-'
    'T7tm>*$nwxv%H99R>7+_)5k2Oj_Mz`85IO<(E8@+w7d~kd!EGZO+yhvBe~avd(%XrTS8|FUf~k`T`@uz$&|wE{u9^IV4U4)N}MT1'
    '))Y!=r>;zLd*=Cb&bl0=A=|CMl7@w8WhyDKU6{4;R{faXiMZYNy$Nk+xm^W2!YXqo~^uKPKHzg&mkdEQZ`OrYlLm7yC(U|fmY*qD'
    '~Uual#8mhpv(PY3{OW3C#&Y@k~VmXF`;b<<p;DNl9H{Eq)+Xc?B6CjxKLA%MPB6ZBC!j4G145#MGQNx2Bkg1w*;es>dN_q1(^Hs0'
    'Vw+tVX`lHgQ=u+4>=AO0%pe9zbcjYGqZ2rZHq(GBGFh78qg@n!L7lPVS|YfyJfu7j&DCu3zZN0O*!qjpov<V#h-'
    '#DdhxB%R8bXlum#Wpl+b`MX=AdH$mv1|Z5f!_3!L<+4T$CVO**3ay|dP+Nl%Y2rYuS}nW2i=G6TXIr92JdUJMHLgW0;^9YVOGbhB'
    '4H>JctYkxSYNo6+$6xD{%IDa77_j;bdic0W5bn*I8c{v5RXNz1zBfF40CxG1qKN+A%%2B15NVF)^4yaEYpMC>^NRRLU>8Q|q{1Lz'
    '%DmYW=t>{%#A=cjyXVNGv#BW*MegS_Vz(qwv6<gXaEH2TuD=;P}77>Yx(Ek&kNf;Kj4&Xp=GMQ+C`LT(Bh5lxzu`~zyreAb!}fWw'
    ')U*uP4qNUZSj<9|=&7Md!vZ7g`R%QjPV_4Asg+>G#wBXFi*w%C_$Ds7e~CC@3f&umZcYheb5%GpY<xz8}>4erP^R(DY;r4MMo=oH'
    'TNZXG7O8f%cSo0prTA=~n`1zspRNB3iqUM}!uK3R;1YsNA&SQh#G#!xNdc1;!TOVLUTgFY27sn$-i9OP-'
    '68mTRIM@L;o7LYL~`a1I&5!n(~wDJ*PMp6*Xv?%RXOmbN|Y6=q4#+Z(%t{*TAv=u0kIq8S7e9;xW;`=P@O*aB@BMJ(W_|WbX4s1)'
    ')SYCZK5iqUY5rIe&+6O`)YQa;o?$kg>dP++-NYO&^@_-v*)8RT;p0p6oEW$b(4L4Ye3;}Xx4#axM5pv2Vs2Xu-'
    'O*!a?S5H7=oesFF9K;azHMIWN3>>R>Bn|X-'
    '*O|gF#HO8+Q3HRby_#|ZSrF5a#3Q7koi{o@pOJ1IDv5dwxztWBRWp#uS?T?riXFB10&g(L8ZPfkyy>@H+6Xy_?=&M)t2(5!Zgo4<'
    'yqh$%;??kQ;uK8m?LHT2l~PO+fM*;qw-'
    '}a?&PYBt7)OnB5l5)5W=q@@v66x>1oEmt(|E*cDj!L?vU(tz=SuViXlhz;QxEdYUT})n6>N+PH_bJtQG2z>%V`<mf&`}hqsONA=f'
    'aewjF)z$WjE{dLDhJ!`meqX`Q1kjc!(6AQgx8O{u<FUnnSQ&qfT4Rty<!OiB4$}I}HR%M1`$<A>w&bxn6=7&%iN*euaXWVL%JBp{'
    'yIalJSI3%X8jnq09N<JZT#bgdJ!X+68W@JaVe_^zBjeN8SD(Dk$lO'
    )
)).decode("utf-8"))
_PRICE_FLOOR = 1
_MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}
_WEED_STATE = {0: {}, 1: {}}
_WEED_REPLAY_STEPS = 8


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def _copy_action(action):
    action = copy.deepcopy(action or {})
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": [list(order or ["PASS"]) for order in (action.get("hands") or [])],
        "market": [list(order) for order in (action.get("market") or [])],
    }


def _seat(obs):
    return 1 if int(_get(obs, "player", 0) or 0) == 1 else 0


def _farm(obs, seat):
    farms = list(_get(obs, "farms", []) or [])
    return farms[seat] if seat < len(farms) else {}


def _align_hands(action, obs):
    action = _copy_action(action)
    expected = len(_get(_farm(obs, _seat(obs)), "hands", []) or [])
    hands = list(action.get("hands") or [])
    if len(hands) < expected:
        hands.extend([["PASS"] for _ in range(expected - len(hands))])
    action["hands"] = [list(order or ["PASS"]) for order in hands[:expected]]
    return action


def _tile_at(farm, position):
    try:
        x, y = int(position[0]), int(position[1])
        return (_get(farm, "tiles", []) or [])[y][x]
    except (IndexError, TypeError, ValueError):
        return "LOCKED"


def _trace_actor_action(actions, step, actor):
    trace = actions[min(max(int(step), 0), len(actions) - 1)] or {}
    if actor == "farmer":
        return list(trace.get("farmer") or ["PASS"])
    hands = trace.get("hands", []) or []
    return list(hands[actor] if actor < len(hands) else ["PASS"])


def _weed_repair_action(obs, action, actions, step):
    action = _align_hands(action, obs)
    seat = _seat(obs)
    game = _WEED_STATE[seat]
    if step == 0 or step < game.get("last_step", -1):
        game = {"last_step": step, "active": {}}
        _WEED_STATE[seat] = game
    game["last_step"] = step
    farm = _farm(obs, seat)
    positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
    unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    active = game["active"]

    for actor, transaction in list(active.items()):
        index = 0 if actor == "farmer" else int(actor) + 1
        if index >= len(unit_actions):
            active.pop(actor, None)
            continue
        age = step - transaction["start"]
        if age == 1:
            unit_actions[index] = list(transaction["intended"])
        elif 2 <= age <= 1 + _WEED_REPLAY_STEPS:
            unit_actions[index] = _trace_actor_action(actions, step - 1, actor)
        else:
            active.pop(actor, None)

    for index, (position, intended) in enumerate(zip(positions, unit_actions)):
        actor = "farmer" if index == 0 else index - 1
        if actor in active or not isinstance(intended, list) or not intended:
            continue
        if intended[0] not in ("BUILD_PASTURE", "PLANT"):
            continue
        tile = _tile_at(farm, position)
        if not isinstance(tile, dict) or tile.get("kind") != "WEED":
            continue
        active[actor] = {"start": step, "intended": list(intended)}
        unit_actions[index] = ["DIG"]

    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
    action["hands"] = unit_actions[1:]
    return _align_hands(action, obs)


def _shape(name, value):
    value = max(0.0, float(value))
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "log10":
        return math.log10(1.0 + value)
    raise ValueError(name)


def _market_price(item, inventory):
    base, equilibrium, scale, below_func, below_target, above_func, above_target = (
        _MARKET_PARAMS[item]
    )
    if inventory < equilibrium:
        amplitude = below_target * base / _shape(below_func, scale)
        price = base + amplitude * _shape(below_func, equilibrium - inventory)
    else:
        amplitude = above_target * base / _shape(above_func, scale)
        price = base - amplitude * _shape(above_func, inventory - equilibrium)
    return max(_PRICE_FLOOR, int(round(price)))


def _is_sell(order):
    return (
        isinstance(order, (list, tuple))
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] in _MARKET_PARAMS
    )


def _impact_score(obs, order):
    if not _is_sell(order):
        return float("-inf")
    item = str(order[1])
    try:
        quantity = max(0, int(order[2]))
    except (TypeError, ValueError):
        return 0.0
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    prices = _get(market, "prices", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    current_quote = float(
        _get(prices, item, _market_price(item, current_inventory)) or 0
    )
    later_quote = float(_market_price(item, current_inventory + quantity))
    return float(quantity) * max(0.0, current_quote - later_quote)


def _impact_slots(obs, action):
    action = _copy_action(action)
    market = list(action.get("market") or [])
    rows = [
        (_impact_score(obs, order), -index, list(order))
        for index, order in enumerate(market)
        if _is_sell(order)
    ]
    if len(rows) < 2:
        return action
    rows.sort(reverse=True)
    ranked = iter(row[2] for row in rows)
    action["market"] = [next(ranked) if _is_sell(order) else order for order in market]
    return action


def agent(obs):
    try:
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(_ACTIONS) - 1)
        action = _weed_repair_action(obs, _copy_action(_ACTIONS[step]), _ACTIONS, step)
        return _align_hands(_impact_slots(obs, action), obs)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
            "market": [],
        }


def _kaggle_submission_entrypoint(obs):
    return agent(obs)

