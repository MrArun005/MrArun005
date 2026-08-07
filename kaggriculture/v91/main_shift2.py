"""v9.1 counter-fit: v22 route with all SELLs shifted 2 turns earlier.

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
    'c-'
    'rk<U2hyoa{Ma`J>P@ogOubqtu*Hqjw>znaf9=MSS;W(3>fE!wciZ?cT1+o>6wnqh{&uSlDm2vaz45$E33OQGBWb#|9SFnzy9`*zy'
    'J2+pT7I~$xkmoe0XyGr|+Kp`>+4`umAPsUtj+C$FINr$KU_^%U?e~`Qgp`-Iq`3ufG5Ew_jeqee>hXt0$j->%$Mb-A|uitigM)-'
    'tCXx`LNr){__9*54)EiKfic3d*{d9)w{Q!U#!;G*Z=#c?~dp4=G9+5{dD}hhk5<{WWW3H@n(c?-'
    '@X6%!_CWE15CeuJmj0Notov#pniJ)?)9fvAEzS*!}|Wyo2%Eqe7?@dPd65tj%hLyGN{89CLcZ?)!ZUiFJJ9$4Pst-'
    '{yw?bt$C*xnaw@8So}G1(bTwy1^;Y_x07``HS(>QZWex!f$y$)<Fhxu^z!5G{pscZ{KdDAhxzp@1&dFvFq!_{wO+lvweQyt4z}-'
    'Pu7`^rK8N;_G%d7%(3rrJPQT07^yE^8eUU3^mcIMpiiHm@)VDBm*Mke0?mEAMVc3Ze4K-(ULzvq_G3@+tY8ZC<Pt&sCvV-jjXO<c'
    'aygS{zWphG%rA8F@eLh3*YOoE_tI)3FCv$4e@sl}ub>A1by^+Od-{6q9$<CgK4;6kH93O9Q?IV6`e&2r><0`KN_^rG1<?nftyO-'
    'k@a^$#Py}P>Fz54jepLg#+zPWnyFQ<>-`Y(TY_i5a+4jbl|d(DU4)&B>xlOKZ@ef|F3PY-'
    'b;mwidP4Xy_L@`K&hY$=+~SJ?=vM>a=-'
    'v57vC)N%?6^T5FVV6%hY3SM(`iAh{E;9~Q;^6|ys(#;R2qF=9$?qtcZP~<on7K}8|+1MP(T3e0D85XU^0F$hjSSiauYjs=&bjXA{'
    ')q&)pc;9D+nFI!u-)!<;ysa&4lq6~$J(BsED6qug)y-GVGLS#CMcAQ5#5vAkpL`&HDDzaoocg(Z%oQKk&jv^T?fI-'
    'T3kkLhB$t5$Y{Trbc#xNq!?(XGgV^MJ2roAqjeKZzPwbV;4>9OT=2X2DvgQnjU(A>|;3S9Y)3@uFM|MW@gjswy4wFouU%fhY`}s;'
    'vA_LCw_G&1pqtPSES7_vee<Kg6c^)Yq2;}hrIPJcN^w3QP*#qA!<~}yQnJgRM=<KhR#d!3o?eW%II<RPj7^O`6%8EK@{Be<RSjWa'
    '6$A^N&A`nLZTsj0fFxp0hAUPG%onYfMrlHLX4yusAnUD+d8S(V88#`M=sH)A_p%pW_fY^{c%;D`HUcUdUGyRPStKY^`bp9rb?ryx'
    '%<uKqd+ZIjgGn&(6Xev(@S?=g(B5WffE0YW2gCh93gFWSFTTHhQBhLKBrz=eUdGr!qM43pQB*7%+AS){pIdh8m-KCFQ1x+v5-'
    'S$%DbmlMx?QLyj=HoquEInCZ`SIb<s)RrW7zeuDEko<>?TX(WYyht@GYqrF`XV;RreY4Z`66%8Y*Nnvh~Pa!;^(`sd|E8S&xHrp&'
    '5sp^ik7G_a4FtOu#3XTi^Od4i!n%C7%IxoN<%HIPTj~^1)4O21OROk8B3Ok!NvAyn#jqc{bKO&xVRoTl=}c>f*-'
    'kD2yodf2(#P=wlY4ai=JoQ1mjS8UJE55lSf7!L1ay8Fwenc%`vp4h=7IYegK_nGlZv!9bp_^)b<B;ngkZ~)_zkUQ>gphM!ZyZtsC'
    ')W0dQ}~DuHkWZ?kf0L!+<6zczk^epy9TtXO%FrO<lh%e)^mmHZ+h%zSr`eE06^Mt3DdBQDjaE3yGElW3WJew@1)R;zUN^6l%Y@{J'
    'ZW17Vx!l!wnl#_{>ZER*@+<NKHU?|1Lt|LyZ%&$VL%5q?RtndeA9&gqAfhe9d@RMN(Y@rCe*CpT&Pa^i|iE`i>?8`U8bck;0_u1T'
    'z`l3|wkP*^;a!<5-9PaR~>CYz`-9)FL`lzx;vTmR?|4|ULTFeP}f-'
    '1+Kh;2NEbE8jh{S&a@uj2JQ2vO2v9E3Rn`e5?8GVc`$2W*h?{*JzT=woPw<#ijU$9i(>B+J)2MUf5oM?24Zvou!vYOW?4{c{H*(o'
    'QCHL7xHNJG-Bcy_~j&u@D4Nb=wXzUo*<6xI~k#M0~=^wypt58&w{kkgU<=i^91)0Ug|}Uvr8gZlXNLtV1z7_G0VIZw!~?@wCUSU='
    '(;f3wZ>=Vva3fS;MR>=j~^YuX~YpaZRdzqPqpXOM4A&S+eEV|ycBN>&#w(?L447}#NaV}#7JMbQ5C-'
    'EVJ7U8W$vu)3_!7U_I%pS4`XnwBS)Qk0*nZeBcQ>RPhe=AOi3q=<^v7VcmW{Uc4-'
    '%3r)`0Rs4Rt*{d`(EQcxU$fLF;3277wIyPTfSb~NUQ2#q6+4znfTo`U&`A>}euS?v^hg6B;@@rI5vJsPGQRhhh9KR)NI-'
    'Dor7n|7j#6EXxEi9qPXgpj~09LhX<l}@bP%ApIOw}<3Wsb(;)7O0QM$#tRK8c@h(J@oo0gMd68f?ScWrf9q7W0dq-dhrlC{`ltVF'
    'F0r{2o}I`k-'
    '_E}4qua$UOL$d(HL*8;+rsd(2O5o4iDTt%9Fx`)ezfqBq7h@7cqs4>m?h&L``0fFokDTOkr(d3ab&A!p*A={S%4_^^t`6?-'
    'ri!r>!Ky5Y`6{dinCxdQc&OG=5-tJ`3gH?vmL$kP+tVCcoHPS$LeZqER-'
    '5a@7S|<$UF{gkc)$m1|KDQleN77X4cIMZIE&je~~qxfj%rnb4EaiYsY)or6*2k?Dze(;>W+7a<%-'
    'UX1GiGd$Hg;Sb_Q;@!RT_xYfVOb%h|oUVmCnMkfExTtd8EDSg}+2cx_tS`=@Yt6w?c|ixQ{EUygT}07rxFz#g=w602S^#VK0Q)j)'
    'zk8eMK*s|#=CGDgzL1rhkW<6!P4NE<GuDoBDSr0_#Oe+c_%M67G!va1!4G3%DgE~7R0%DToL`2-FKaj<`~v-'
    't)=Vr?LyDrPgAvhUpOw8$?gJQFK~4a)mMU4il}eD#-6P25z-'
    '`vgv&*b*7N}#(BNjvw(vRj$!{a3zDZ8_lJzE~OaF%E8f<TGjORk^Gq-qi(GkBIjfD7@~o#I4%yMuQdOuSu&ziez(lB*BykpqS;CL'
    'tAuOU@5NWR!D^oIYMA1B0g}f>$PzBGXad^x~b>!p0G~t`ml*LOB$tui9Z8Cs1MZaB{N@22FCoUrl>r@S6<r=DMRU$f0^7e5QInna'
    'kaOwR;ToUdJP5qIS_LXvRgC;0bK^|A#@>GamU!J1O<~YHps!)PNU$xlTSLzuw?MFaq>4`CEp-'
    '<VLF@ib2HzFE@`qfuG8~DvKlD!&+*hyA{e3j?IWOI$Dq}5v98Y7@|s7SbCmj0mz|+ScG66OQRY`g^_8|JHZI#X=2lq=PAOksGI^C'
    'oUI`VgR8SE!X>EQLU2?w0n9m&&;VHt^YBiDDl%&nR%03QTYKF+FLZO#6QLX3=(1wze#pf*tfCPX-sOy$i9tcR_SbhuO9ted3f&Wh'
    '6;{e|(1DTNLkEDfn@&MJ#JKa7G`s_S-'
    '73Axh1^YKNe!7GiZ0dkSd|IP%wr`BM2N&9PI=pd)w~Fgqzo@BK`~~N9a_0!OFNLDEy7Ve*55)FvgGdwX;3aZg0~clDn}Lc1G_v^?'
    'c&rt3A+r<xX5H;RU>-YnQbKz!<tVv3~ihpCljeW0%*Q879_8G7b;K_c7Ud)NeOe4nF@&jR>RYAA`jFx7q-'
    'h8B(&2Qpc`l*#%YS`a2pS~0(Eh+FcZ|acr)}&*prTtw^lAP!|qav`O4ia;;cm5@#T`b1*wBDp;U0qL3076iuh?5R|h_I>qE!9GKH'
    'BQyev_%M)0DU1whonhQjV@Ti2UW!OX?ziU{7E3<?XNcy*XMtgOoFLS8_|Ng9jjlZ8Y~z$!bjg+Lae>qOS*96G2xEzWW#r}>8#Iq}'
    'l<3FNSxfi?hA+V<pt>~p5FJcEGvZKu-'
    '+rzqxJ(!8x=A0Q_^Nr=kW08!Pgx?O_^g=mhU&<izPtv@%25>QHN_vM#Ly*+8Zhlf~LK8mk;v4g{eltAJjj03kMVGhr$l;H!R%OMS'
    'p9a4^#Nm{yj33YCg7mop)Zhwz}-Kp-dp8QRXd!<9zq@eS;2$BtOLnb#w8II%4d&>JG5^~bOR!?!oPVM;9(E3%nA)lF>R}82(<$!u'
    '6Hdh>|!BYyOOU$nkdaSHiW3;Lc371hWeb8vswSv(b>u^B$i}jTP&n31__M=^0r$BfFxmBFRXswbiC6k^&b<;q?2cvo9|4hg}!?Y&'
    'ZxGIDqyE$P#2G)UP=Sls@4U`BEaExh)KniwFn1+DHA?-67a+_I=o20p1zTq&=6W!3MQ7h}UQx(79!ln1-kwP$pMmSnii<Lm>9k-'
    'G;Tm$=1$`WoU7Hy5q;`PKWhO=<*+$MyCAH7ckL0$*i(@{39SL#vH(@9+YB1zf8;!a(pHs^{Q`F1U)9MS}JyFl7j%y=##@46QCXNG'
    '9Eo}__JW2U84Vpu;Hvo*Z5E=<1RG%g#PK9zEIh0f~@9T#SX;&Qa|prnebyhe>qkE}wix@lz94=me|X2oV)fmTvXRRhRF!Eyt^QLQ'
    'D3p_VD`U<G6(3a~s%F1pBX&M@*g&EL0p{Fk=S6h~g1)w^u*oH1z;a$&6HyS%Qe7bKcobtWpCeV&qZ=?>4X>yilQ`c4OouP5WRE8$'
    '|53z6ge-58wy4A4OY4G{Qrl>{}cCa7-gL%v$VRk<-B58UWU@&ZL!qAv*&IdY-ey+%%tJPUV@e4LS*tFm>2DU8bD;arH*0K&~_4NC'
    'W&f8c{MgH*VZt<(J^5uKzN$&-xr6E*~Lq;k>cGbJXSlQIKQ&z!@|4{>Y>cOTj;#Zs<woKD4g)1qXu@PsHw%gg0YOXen}p-'
    'W_2V>LtJj>2>abDE&dvZJ>TG6f?Ym?fc?$y(MDzZu2tnAtZZ!Ab6iaNm)#LRJt;#Y4;PM5f>shqE<_ItibeWF-BVktXz}LvUpfYq'
    'Z>AgXE_JZnE5q*Oze|%SVUq;i!qp^INj*j_f2ZiUMy8jmha`X)4vs{RK+B=9SMKJ~O%ht=4IFy;U{P6-'
    'e#UxPRaE(rdM0ivHE@pbjwG>!G>(wN$^{s1F9k9G9ar{>LrC@8)>4;VxoZ9DQzc4(0$tnb7%g>AGyvcqIW)Hy(4?Ok~@f5D3<xIj'
    'J=8J{=%;hUosAkNNJ?^C121jn+IaT)$y`DHtF%pzQWyWEm6fXrWbLjPAaXdw&F0z<BS(hmOAMyU~TbfAb<=RN4q5rCjB6S{SL-'
    '_LhQF`jW}`nw^Qv`t67~Oo-Vho`K(~prmo#s(^7h_l;uVHbq?1K5ArH-'
    'P(r`d4%oK;=No*@&=9%L<@t;`jSR~SP<c0c??rj*y{lC7*hxyNutskoRig_f3?zsR$Wm==N68d^t)+5g>0NCMkdHe!GeU-B-kxeG'
    'NpI8ZHzH&dyU9ACWa*`#cGkqSoXagPB>XV2Eqw_8RP>NCX|E`yvE5`j3oe03xu7KS~Z#KYEdEyIXN;i!C1;jLXpiHuQJyCc?lxCt'
    'DGKG*7+d%bCY$Y6aa|9<d3v@WZbX9P2j^YMl3ZB$D{O}G>gm&r4;a=R;ejH8N1awdc)tUH46uj9QUG!^`knB0JUTF^;(+!vX@C>u'
    '7T$iWr6FioZn*^5d$A*oK>pEDacQF49{+&(ww+dRgblxYs^HRkxR$dn{ayYEfIv28G}w$$WfES=VBVHnE1C^q^k2Cpe<lMqQS6GN'
    '=&bg8JHCaCV~;d;ARhZyviszZkZ`6<dKw_(L%S{oukI^38tOM%RdwMSAZ!YKa*U+V%$7<8bzxLr>jtKmdYD-keebaLd)4V=^i805'
    'i~BuTINi!vZS#J_p$VWhqW*yQ?SZnLJuI@lc%Bdd6k!E5Lp98c94Lg2Zrgv@4VEG0t3Z~rkHlu(u@z}nK(bM>Re^P#rc^bv}g{JL'
    '9Ea?&gqTlYH(rK!o#}+$!n40e3H~}P41ak#-'
    '2YSXq{UeiIY+VcL8m9RF*l#evGnnAvegoeLnLW+418xL!fzyLS2|#pJ!Lj65m};Rs)vu$GY}4t_RxS6`=}E)G%pjwhWGy;|;7-'
    'ir8H$3fMrs2Vd}^zdQ;%(4S@&xe)pUOHq-kQrwujzE0|v2|U{C>1&({%jf|zKL;zAn6)EY+4im@Kxo@M-'
    'tn~($UCG2x8RDdkQ3=ins=Evyz(6^To$K?>)4JH(jEHvRnaHE5tbeYVJZFE8IZYv{9%aYlnRDjV8=|yqT5CecCbhG?p!rbh(C7h^'
    'd&M>{wQxCq7BH6@Tg8oKVUUo#8^59^492gDs)sNOUqPds?lRhPFC)t8u4TVpfSN5NB40gSO*i&wW)}M>Ty~^w=x$Y!ZV6XxKO1Xl'
    '+D#;c9=EbC;Ql9OMzETz6790uz)gWs43_R;D?pyyKF-S^jE9cMyd-dN%bB@BF|NH896wWKp{v4|9*e@MQ8R<3hAE2)-'
    '?d%(+aDE2ohAnB!oQ&I%H2*L02gHf6lp8j}u$8p|>IwuW)FSqApG%8_*S0D0Es4TX~N1cxxXSI2E3X@fOVqAkti=iP0<t^a|F1N}'
    'Y0H2@#nqQ6Y30!)2*0OJKSvh-T?k<25W&^IDaLa-mT!NmbzBNwZsB^6kY6FK;i**zFF?oLeJy)ZeRWQ(X>xeV<@wN;9L?j+Yikj}'
    'aijPwUX|s%)($#+r*48Qe`?ak&{q0_`y%b17{k>r_C;&oe!=B@itzB-TS9Pm(q1w!7{lV6r!(zF$J8Nc1(RVG`?Hws6f$*PY?{4E'
    'eLvzJ{yLSEt)TkOE<&BRA!+br3_G{Ek(`A*-YJyCd=QA*Ji>RK08lJ(g7M9poiX&JePT4u0$9+5mwX-'
    '0CUlNQT(1T>L!#o)m2x@?d&`)RD5*h2@n6N7KnAwhATNxxyGL$0ZS+uAM;l?&&xyh5cqRuCSUXUzUy_sV07*`ckPxL~fHzTxp{*P'
    'TYV<1~NoBKy`Nf*~{8jxP_+>`cbqzGi4LO?e@A33PP-'
    '#%R}yBY)vFKet=<>RpvNKu9G0OmK@TAW(F+Cf(U6i@dzq@%s<;QaxzhsGu2TzK|h!3p{(lQfNn|9St+pX^(aq3Fk*aj$+1`m++>='
    'DpvZe_h@?#ZE;N4{<F*%Wui~79i-Zj7%KQ#m+*3Jxki8zaj}zQQuuHSrdM#zID#gnSG=*d}^g0<-'
    '`{($MkO+LD8aK3`Po(F!XpcxJ)^2F4F`rwiNhI_fg;S*ueLzb(d|pHD<CvTs-0KbL2!-^xh!UfY)a(K<tpXB+EE-'
    'r};GXRaak=Ota;LqRpi`?MwaA7+{Q#C@;C1OP8MMSS+Iw6Y`k~fF!S{}+g@U{oF+Ak7f)UudQL8kmTY*xG;_P=t%%Z0T$8-'
    '&Zz+Tw!sZ5{L3@vJ+p)vc=jbos2B4vFU^Os6ey(bK-i6Zo~(&E9`^T*xQySEX;dMocmr7BylrP3!)u-'
    'Q=8P+CzG2*b{(sv@C`yy4bPa4wq_T+a2jC)3C^5MyObRhp5*28AOzsu2zj8R(;v36g&%Zx_^9>C#BzARJ<WV41_LNn(@MY6()59E'
    '6fdyK<9=Lg_dsTIy+8moe+b5C?mRN4y*^)ZD;jXQqseM@!w@JQ8$o<&w`*0wQTmI+}-'
    'hF&F?8dw8U8J{qnjt5432RwQehUO1M%DVHgW=kOX=)32rKbYoNzOlXntq)%#1gSAg7F@4gi-'
    'v|d8C+2i9jXTn`#ASA=ghjQziZ(nebD$%TEt;n7>O|9(bv}r3FQ+L*UsUpWhto*X6k+JjL>u#ts8x4=CaN&71>mwawC#mXcr+Qvj'
    'm30uFKLle?5etm&+WFRlp!bR5U`gC%T}TstD&4B1x*X>r7{tBr?!~2`i)eiXQ>%P5wUOd&*Iu9<^zLNkaGT&7HGqq1L3Z7wFgHZm'
    'TWDsc}f29c~cf4-'
    'Zw%KE)kJtr=~2!#*V&<N~ucuqK}O%FUV~}fH#{0ps1HRz;f`#D5n;?37MV9hAB%sSZ!`C24j8<2xMc8y^J$XUNdUWeqb@W)HObXM'
    '$z0^0`BX~H&1cnACQ52o)AT!UbnPz8|tz2ylM4}?irOK>&pt9Mv(Hw`61=UCw;1uL7Q;#2pAaZoid~^#WPFA+atK4s8pM`Qtg(Vk'
    'MN_sAC1E388Y%hD{w`%l)y8kzB&yyC_PIdL@io_yq?`=;ONXy%p+D#hdcrz<*OcUK$xP;iOHU~h`RB-'
    '3Z+YYD@v?L##qi`j22Z|@)fu@U%&b1<aABN)ZmOw)F#()uzGMHr!YmAIRV3t52?p76$XNc)K;nf=)UtAvb9a(w2u4KnfXcmYCcX*'
    'Hsh`(hq&#CoT~fI_rEgR=q8v^AbTA+La>iakd}745hr0YEz|ObwJNaPRjseA_gmV!yj7<Exz}mrV`g_OQ23(R2?tUz%S3rZ_bqD>'
    'q6mSbjc{q8JZW@q9MG-V<f0PwRH2e*ktWm;RTK8yeqo7X!h`zVy<RxkObFB9gh(BA#2U{Y-=1dg7?5nWzP9P1=TXoc-qt(sy&J$p'
    '+w9GYLCnlG?<;<93Yn-1wZ_a`KR^k|9El;#Q%ABcN6c?i??SOJR7$Z%m*Tz{-Th|IPMr|V)9c?!5Av}MV`O4!u8o=Z;3lj*R-'
    'LYOVj13!J4IFOPUs%PF5fs|`qiQqu6xRtltgDX53#;e<Pon_Ms0yxO3-{E`j(q6^+i7s2TG_nVmnorr7CEk4%fpZyV-'
    '5k9j!1)yu`JWGH<q1>st`h42$=0pnV(u7!AP;r=QWLo{H{H!ZKlDed=2oZ7%@iWON~4k>y~ZxEh-XnY5YkAdKR0Y6QHdH#$9$mVU'
    'p@EslvyR7fGN`{a;yM@_-'
    'P`~=@DvfbD}D@vVS!LXm)60{cb`g>b;ohp42J0!sq!m{t~#G1UU@F<oWEs6d>)i%^koLA2HTBLg+dtv5pXaAJEeJ!RflnN{EpeNr'
    '&%bn-tW#QH+t+5u^ore<%YHZo0xz{^xL7@{4<|8A^O}z-`f8{l-x|iNhmk&okU~^u!XG(A!r74hNnU(1-'
    '1wPjbzt6z~g>W%K;fg#^Q8%W=>LUn3n-QudzFX8#*^~Ha%^sb0s4*xzK^aQ`10W~uv0laK5WK)7k9DmQRktmO+@L3~-'
    'shQn2FoOPS&JzFU7v0kcAk&c^x%tm=YrWGMa5AWxQlj>!t^8kNApc&Ivp;&-'
    '|3uENe%gKDTpSdUiV#@7QdN#)lwdZ7F9zfh;gO3*$oh4Ov&m-3<5B``tBrg(euurlmf@wJB;+5P*O>O>g!&M7k2-X!hUD2`2<_-'
    'J@y`0K@N$Sl8f)fDHn||A>^5v)vZE}W>FNEsWtC+YIk=Ic-6X}<0&xCC!wrLG&-MfYyh>4ziMf`!(UjC`N=!N2q$N<M0-'
    'Q#w97!=BKU2i^+6xp@y00fK*c9rUhEnJkxtVgWF)6S&^}e>B}br+O_tIqT`$a){exhP6m49L3j2G}C0$9J%116aTAN;m`7AFlDpO'
    'y(le-t@D=CR5v{x#xXA<RFdZL@_u}!&%2k-'
    'qhT|=jP*%1<@&C1ytBU+e*M7B7uYNZdMG!hrUA(o{h&=CvXwv<HaBC7W|hwW*AdJfN3kZBYpf%BCj#LlpLS64hVC$(bPVxb{XQ%='
    '+VQU%n64@*VKEfLcs#R(B^>$mbE1V#^fw(^2G8Bzs7TQZ`g-'
    'kdxF3ENV4P4dY`qj9{IL~<8OPt}^z<$lq_*wMntnmM|l4W435qU&Q{!1|JCt&ovVjhAfJLELYld>-'
    'q$$iGE`8uS!gqKlH!G?Gz3b<KQ2FDx%1SLtPQI6R@0$09RBPL8|_C7;J=;!2~43Q7SQPdIp7Tk2;pDWUU&kKorA2z`CV+e#%6gwv'
    '?+U;zu@5Bf(reY&9SdGmJ%sa`)6mgw_uZKjHvpv|^G3s6D>!laGKMiQqBA+%)>>mYA3PJuuy+#jSOnx8vsEuHiv`eM4GWRn@1m_u'
    'ejSfiBVLEMYMrhYIxq7i)%8dLO>R|T70O&aY<f*TrQL)mdF)DBaKy#*CjPeAN;c4#z*^(75EXz!CD>y`t01hL?f#Ik&az$oi9TVW'
    'W6peM%bm9TEafg@0rzlHe%UXs^9@5r+3b4+r~LNPi&rC1AVy59}xw!t}+=?x)&kgx^N7ifqEuAX(FXd~M=WI8$E5e02e3*t(VAF&'
    'dTePL&z`PElTz!>70Drp<B+{O>x3-#_Mi-4c5yf!8K4(&HWOLAiXmeJf8nk2x!(hO-'
    '*`kXTB%qH_4Rn8R7+Gc2urd?xIJ5&nf10F8A1Lk_NHJ&-'
    'NpRI^Y0$^Syj;3Y{(w14Po0VQ_pP|oN+<Hm6bssDsJ&WLDe&Q;32aq9lJ2Ue6jiFk^?FLo2FGVXY4EkKaq*^=4(vs(GX{0vT?T)&'
    'PEFfb}w0Pz-BKj$=yyZQ>jHE`I=~LQ`nB=l_)Dk45jWNYhT|c1Ty3!{~=A<9S2uATi#rIi2oNff-Midlw!%5a99N3novAp_fB41j'
    '=qk&oz+6O}HYr#{p)>We)J*BW41Ztt6x#33Gbhw6=CoP0~79k?lTxl=2+7KXT=0L22Tnoy>mKTszr(dor<uGtD@Vq#1?r09M9RWZ'
    'ETnOTjm>}Zp6pk9GGHuY5+p~pTmAjE!kgcK63CUTa_`*{eK2gO5ncS4#r>Wa2EAA$Zd1aTDyVt}Fa`@fpFQgV&kXx72MVmB`;)U;'
    'UeiU5P#7C3$-eMdzT<sTl=U?dZrWEi5*cS)mEuJRiE|Tv__r-!@XP;v@uw|Ut_cjHlq!<e!$SR&BKB+1ZtEq-'
    '0rRVB_Xr8RmS7uPtgMB^7GkeM@?pUxfF6T7YoJQ@{W4_aJ!UYLT`$v~ekL&}}-'
    'c;L;(d>J)Fs|^w^NQYxWS&x_kU!_xnN}<i^+bJyL?IJ{r^gOC;J_rMGy|SS4n-'
    'CvO_<6B54^C3H?NeNJHa>=CMa2Z@_N$$LL63}O-Bn|7!>HkD3}q}+oeg{crt|;WvQHTs_Qf+t)JA$EO+^{Uh4Y)0N?fK3I'
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

