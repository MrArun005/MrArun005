"""v9.1 counter-fit: v22 route with all SELLs shifted 1 turns earlier.

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
    'c-rk<O>bODa{Ma;o%f*rphWqmk$QK8<wyg4xUn7(g8_C81IGF=_Ra8rx3m=5ulq%2L}cY_k~_LlBD-HzR#v^r$jHc_|M$ti|N7hC'
    '|MuIHfBEj`CqKRX@ZrhzAHI9?AHV+BU;q2de|`DK-+%q>KmYbWU;g#;lONu^-'
    '+lQD{ip9g{pFXJZ{Pg*^6JUw@A~k=ZuisYAJ*V^uiovCe)D0sd;R7A_do1je*FBy^Vx5H++DqU`}v2}`uh6+{_x%LT;9C;^QWJVz'
    'xOb&pP%e^A3olU@a?<zAAh*{@zwy-j~@^D=3}R3`7)@V-oJbO>D9;Sh{3SF|MceS^)H{F^YPP-g{EVgjD!s8@Px@9ACGEok*k-'
    'lcDDvGpFICPdDyLarw^IUJ$P9BcjTd|aSsdr*${6h>vU@5TQl7(e3OCio_XW5H@@`p<L>?G<Nx@@w~vSU^&<s~Po6ND{@t@)y}Y&'
    'W*FS8w?_{orhaUb8?ImeiXaS)yfhV1Qmapl_qYV2ZSJEtf_r(<pA6#hM!pvO{E@Zmv{0W9(CqC3_&gejx+d?ty{B>#=cKV;DWx-'
    '>c?Fna=8Vvk)x_Qgyg!W2}DDL}whTx}W8={{=yY^4!)SCU1Ir-_nA8>n+#dqJ}lDEn3o`*jwd^5N{-X858-!(t?AI7-'
    'KD*?Xi?tb~tJjvb5zJ=@@*Q<9|SG!jqfBEC?{l_;~Z~pD{6<q)35AQzpE$ec_eEt62PsQ*0a&CRtUHv04o(yd9ja>F6=@?u!ee;9'
    'e)@&&TozLG0!``ksA;u=gk)$D~pfHaX*v~!W=<6miQ2xaSYaTX)Z~`Ac46fh&A}adu>gc3NhJ~WU$*^Elf$qWMBSEV%xv!$tXfVl'
    'oiIuVpv{uJeK!QwIQyoYic8~i^n@M2s_{}Eo#ba$@qa+b(_ekdVpTH7_pKd;KmVx}PEy8XtBBpT;`{V=pU74o}+&s*2eEZrsDA+1'
    'N!FGZ4GH{D+m|s>elxlkT_FH8bo7@`V<7T6gud?nvzVi4MgP!D0)kh&~&XD-UjEO@|a@9Wlb^Y<k&S;)6kMBljlIioOSEp{jb;<o'
    '?^x?VPl{C@N+s$5!&KLhi9@5}_q<A5a#|NOZ`ySFmHyLCKe6yJQg7{{#Y<%6B-'
    'iJ4$Zx2{B#3<$3S60+P<ByAk#o8Nx9A6a{i$E9wbm<V}z-'
    'j9UL2@$W@C0E{BB9Nd$1j(_nGgx_9dSHcLujevm*vfMZ_MbzWG&g5!>@mM`Tk!WqijU5{WhMW^EY{PcjJv7hXIG#W*H<uqd856rZ'
    'Q!b<&M54!ZsqhGI=1rK7y}1*i(+S#Uu<d;>>S+!ouV~kA8#?Q6`e7PB4u*$kmEe&YUEE_vj;6LDLI%x4l$3p*c)Uds`cs`FKwuOH'
    'US9Gp-P?fZ0Mny5(ct{hGbcHWm+yWXj->W`-'
    'HI2HQ;0>Wd~>U&J=qbY=iV@E#%Y^W9gzEtcWu!VBx>%L+q9OIjGX6zL_1Mq%VdYPR^n7$hzX6=iLup%zxBZse>6O`1Uhiw+-'
    '61xv(`<M?Z14A}VneK0unFCGXe6MV_Dg#ee$f-'
    'uW{U@QGOUGzRX4~)`lKQc{Zz7}XCuD3h~lQl=nmLdWc;`n9gR0W<Uc7##1s$vq$OH_!6fQ6n%Yzkxwb-'
    '&w)m&&<yBfcyE9viYsE9_u%R&H%*^eyo(!;jE6tEh?<TQ^w>tw+Ah`<|)f4^d5qhR^FB9E(lP$an9qZp2<f0OFaP(w$xBF50S<u3'
    'o-'
    '<UDdwPf@UCX6W#LgeaN^zznEn*KYV=ua{vAA{rkUs{@0~;nIO_HX*Tm5>Bl+!aPm?}rGQH6I5EBue(~gxwjU?1$m9{|w|ApD<mXQ'
    'Q?2Ky?E30G}r}T;>i*tC&EGHdg$|f6z!>b+pX{PI=<kZHm%<uvSEeF$o2g{wWq6V(f$++^JGMiQRu#G4&R<1fda23~FBF%nS_`^>'
    '#mVuC0G)Z0CL2rQNrTB0T(kN-2f-qd-1<0=WjWM$Hc(fOGW$fhc8Ce`o!*hiTd9-?lF>wt1<0NA6E-'
    'v!uVMLVP7LM&Z8KHH6HJTUiB*o~nfUJA)Ipukt%x+<(c6u%vYXjj^wo8XJlQGM@MAm#TVQ)KuZi(*tY&^44W3+PV)uSMA>&C6eFO'
    '=Yp;)tCNXNgu%wYS(ro)fCuM6)UUC>|D<*9N&De&}Ih@N(WU(ihietc4$Xm<jvKGN;yd2B6wHdu#3HS2Q@*&Qa%{0OLgD2xxHSdl'
    '?!hQ`kx4`9Oy>UI0k9UD`$19bBLxDobJIKc7~v6ck+`@KrK{W={{8m(yF@jz%I8rLoiKFkb@B6ijdoNtdD0>PP`7c;5shZ|Eq~t6'
    '|DgmFe5^rP}1}Mw<~I+KF0D$Q&3*1wtPtL<LskP-fbzgktR|hc1AA-'
    'I7VAy1}?!pgtZaWrlWZKq8kl(d(lO!t`_qa!vjc8Ann}Bgd;vdELq&$jC5aa~n+l_~z=*IE<VtlhTJK9v_YF<|$Q0$>6QhKg>KLZ'
    '#5!^4D!5uKGeG_MpCzM#$<TT<zMHR!t*Mou(mLTRR^YU^V0|c6v_#WBMI~GExg@N+ew5WtPdQFWz0|OM1{0c|G@Gr7s}4vrL%P)B'
    'h2DWzHw+};dRoAM%fg~br)!r^Oeuih-s)-u0}yfiDEri_G{r6bsU?GgNE_B7u2tr(38-LE6IDEnNhsx>FIgXA-qHwp&>|Kj4KB-'
    'Jk`44H{GJ~?%w(PyeUbPL)bd2YvFDtk}C=>s@zWt0}d|xxE3etjkD-lb8u8%(4|(sLDp<^Of$;v){ULcG0Me-vDybXF2DB8X7{-'
    'p{1zI;wo$&6m79=L!|P4({}*Pg9pzH|t_+CR9VYN$_HJn|I=O-$#>7(k!=qD0v`BJ(85+N=;)L)E^nbK!VsKeeymT-ZTGr**+bes'
    '=V-'
    'N)`H_%n8<m;M>SA(n#+)(2gb(tK^LUL?*#CJ%7_aV;oMx>guk+L(i?AbEaTe!6|cR}z&@FCaFw<C;o>@md6A=uZ!TQ4zGGp2WV+F'
    ';`CGW=y@tCFmIa7HdOY)768|A?4ih;}kG@@Lm3C>Xq6CIf@_B7#gN@*xAG#=I9iXv&K?{V7aX{-'
    'ZnatWY+N#rYoP^eK!TP7csudMHIaA{xl?ccOo$I{B%!kNxCp(pY`*LqByqVy0}z)9=B+@BUX?1vD6*?sotGFui)dBOmEV0^Tmk$s'
    'ggD6|g1VJdODPFYb#EpqI(t@&hIZn}#O_^#;7$Jo*cK@Q&439I+nO1qnr5lyGcDoX^ohbcrTCT7Ds_bcLnoX%2u~WQauw;;}TQaa'
    '1gs7QGYPK%OQxO?jT8%o8f6fCgu4NJ8V<>`d<z$`K$xMXEriY)3fRtcJP07om#58imzZGW^zFH}3}Bob;OLMmIweX9r)%g*UA75E'
    'kC$+?a_$LAmzV-*%&7`KChWpRmG8;SIVRvh%V5oYf($6ywZ~lIhmay#syRDzeH&+sBb5c*%z-'
    'x>UVm)gUl4_evIsV1q@G^0o)7ZV_Hd8D7>6#i$zD1#%TTN`pELRP`kB`#LQ2{CZ64j?e?;0wZ{&Sfn^o#S+@(xoQ`ux=Gk&XvRg('
    '5-S<e3(Ur?G@n)&usC~5CP#Us&U_Ip@IA7Sh@inzG+_s5%9)fJH<`bX2w-'
    'JAqfSJViNeZ`5&;R9G{)&V{UwBoqq5q8H(7y+I9ZYj3|l<$x{b#uRhD#&yy0?@8Fr#2_8uxKWQ|{ndql3XTaY>kQ%VJ2UTQA+!u0'
    '%PYAP9pjri>qR}emZII={=8o`UfJOH8&4ruJIwspN370z6Yu82U-$)K<RidTm@)|nl>*&$mXV=DDx`eY#yKd{P9T-'
    'R4ofUXk(qjO+`JXy~2Bd58BA#&ozU47)5oPo9sq~r+y*jG?xd76NDnNO#;%Fzp6^A?JWcO@ZuVhy6IvUP*tg{X_6cnmdI?LJ(H5>'
    'QHN_vM#L-'
    '92d*h{t4DKFV&ki*CCU3Id6FFcM68R>>PS2g7rY4+Jz@S{yqx9xcDLbo&zO+*)RQv?oYF@Km>xf~+96P>qzO<JZkHIF3b`vJl^VH'
    '{8)n5xDZrdrI&lN^w<N)>>2+qjYE8S5I-7&i35wykbDTDF@UmvAtrW22UxBE^)s)^jKL5M>mOygv%(y-'
    'ZUC@tzb;Y`X21fx0t+A;8n%e$$qt~>l6r&Ah(M19Yd?6OUa}+P~9|;2Exc6`F|!9pf;^ZHm(ZI$Zk)VkAd}N*?Cewa$6<B4(u@v5'
    'lF$#3DXeJIHak@fZS$Q`6g*Dmk%7qgrXZdHELzOcB<kRT)6aX?i7L{<ic)EEmke1_u)#Kb2WCNlqK9yEIKqci|rG)9?s&xbDI#-'
    'fb>2I1dnaBr=x^gFY0q;kAq-4r-'
    'U5&Wi5bo`k;P|yI&+3T3Gq{%r7nKN!yAU&n4tt*P{MRi+1Zta_BT>Izv<XL?)(J1%`<_oW^Cn=~F3_SLnz-kRpnOT+X4>LMo=pt1'
    '*z|WYuWZ?ID*;VA+N=D>h>VoJGPT5Bkat1iM;G5<@Lh+`$US$bH}PC^<u(AHy)lIL+U8S2_@(DUPu?tEZ2ObSz=g4c78K8zLN&#;'
    'K=F9GSXm+aym(x+I9_*L6_@^!z66UV*P;6v3R_Z`b0I3j!eUEt<<|+zrC%ykNCPbz>j$(Gsr8O$UkNWeiLZ$dL=uq(s~c6gjQW9X'
    'UPnEZjNraYkyc%GM30(3Qi(xe%uTgqzc9O81?A;7yr9Drd>o>3))kPST9zNqYT+4S`&#T=e-'
    '&iAm@F%s|vL=P>h299zQOhhdgtDc9MjUUA;ED48t0Ps%a$a{1Gexk<t364};R`A|4fm@=Vca^94J<rpa|h2;LSjI&RBEM_fhiQkM'
    '9cTD+fNpO<$5birtR>%rM-El|BrF^_zeK=cysBQ4+{FiVpw#`dThv3Q}I%&CG1j$babY;00uP^-'
    'A%SVSE<7kY@^INj*j_f2ZiUJRY&dE`oX6_bH{WULe9^pAx+1E~Cz^Fv(D39ALqF$}jZ2V)dmtLz4Q}mB+n>xU3uUm8XYpH(ud@W!'
    'YIC0z!{BAl&4tNny`{?gBwZw4TAX#P(Ae0H+50|dXChb@f0CnRrhm-WS=^zl6L!(y--zFWvW++4_b3W#~zn+KVcfS~#$JX@_)|Y}'
    'oPYq?a7o8POw4;SqYth}tBKQ6XmVlAni4Prp)^{U)26;Izs%wNXQLgeit%}U?fn?|M2$lZGWPF$DOqADeN5o-'
    '5%s%lK{F@3&8ke#P7}o%+p8=makX-'
    '7MRV?2|mEnY%!FG5d2Oew(AaEE|)|WH_#DWM1%VRL3!d?f6$7p05K(hf!@Mvl0AML3EmseC#zl9T#I^OVum<<XA&;$nQu^{0z33k'
    'i$O^0`dLqWo7lw$P<JqfolWbjzZzPIg!ll5aDoX{VGBWYnmNf_2^oQ%a-0^kNg*cqu+lc}y2C6bVvBO?>^QbrQuY}SsIaq-Vf5aE'
    '60^iZ?T2hm@ptXHJ~OEi-|(w35O7YjFm55pL-'
    ')HocE(v8wAGA|TZ!2h&LP5qlOso~Mv09UP92!?VrjNadmsxtyCkJZ=LeW2Po2TveM`O1D<1<%PzgyShnAI$g}1*hNvJ3BF@30O@!'
    'dsqv)#!TcaxypRK8L9{B5}8PuF<3c8YN>pyL8>|v)}iRudyYCZUW&OdbdR%M(O?oNC8ih5H0BC|iD1+)IPBpe&`Q^F8t7KLaMU<E'
    'fp4wH8bcuWkXFzl%8aljj%J%k%s&@5*|Ic>p(>nFg@UtG-'
    'l&7z6j>2k&VG>Y(V>o@5hT_!k%E;a^(x%Q(gz;a!jMnFDvJp{fNW2mn$qW0ULKpQ0b@8wHPJ)B^on<0YDa;A;)GI6rE6)%2l7Fjp'
    'H~&FvM}QO%n({02gx8-'
    'TpTC#I=UKM*j4ZFJRlh?a&b@6_uZ3&p<w<ppcQR#7*6UGIu=lsEr8xfWKOYnqikNt81fF)LeD#XZ)XTJFHxu~mh1Bzm9xZW&dF-'
    'P!v9#;zEAnBqFteh8YV5xI>rB0)elxGMeJTKe}E6GT3w+6mU;ghC>OD|nG!4;MG8o9XKH&=S(Fv*kHCGsw!X&2aA2jRHQ}fS6SH<'
    '?D~oP8cDLiJBye;{rR|U#9-'
    '%~ATgZttG0odg9DeeBZsB$l(rJ7A)9^8OvJ_71)o+BQ2T52;KXwLWE+BsxVmYOP;bCAWPsgHTBZolPdwh4UnkU2`J9hdK87hCfcO'
    's$%#?(pa2P~$GxJeHPc`Kx6g+*j~GSxV7r8YSn>X;faVg#Tu!5oJ~e782L!NhZI(qU6Q&XCZp%sPmWi{cV4)Zh}z=IVkv%o^}7$F'
    'apB1ztJL62Ke50?LG;Zb9F?aimrCW);v#wO)gwya1O_Mfa(q2|*+H=f~GLArD-t&@#;SSipsJQZXM0Ao-roAWUjm=hkKapVMX4`@'
    '!+qlyF6YPsB(ML<|(dY*N9+`DNq1LBDR?ZD*Y~gl~nlkIa?INW}<)<^)Qy)Jk*$IW<r10`+!CKsN*|kMLI!D=bkVbQ!~CsVz%jx~'
    'P$6=~d&kZioEz^zlwpo+@zmM1I~J)BE~8jFax5#`)x8_cCX*dWLt@SPkZbR&A=wfv@iq>`ZB9wA%5R#nEE~NbuD<G`uQXYY=12#f'
    'uE?Ca<{Mbdf;E7?8P?Hj;HJpyTJ69@-L!EEp2&A-pHanvAx)9z|^l6OvZ9;z$eD_bQ5=-'
    'R#2Lap6r2d9Ku`hU?2$r@K|rmE4hIUJr+@gOKCod#vIPSqFW*I}*PlQo7zwRmNt}V@bb$ycJWPvLOr@9TL~ewE<++-0CUlQ-'
    '(OOT>L!#oD{MfqG5W1)KRzAh2@n6N7KnAwhATNxxyGL$0ebjuAM-'
    '4^yxS&h5crIuCSUXAC|5lsZ4&MFi@#PL~fHzTxp}xCvHH51R0_npgKGLMrQ3R+`>}`{U{2bnX-xCc6(h11;O5f%R^2vwk8rsKfti'
    'cDsvn-'
    '*GZ6COAcv5GXpkCLd21h$l?@0NB<KHXqKb{a&;6=(9flMDE&IPwp*%nT}z7)#`v_zQCA1|)O8Dm{FmKfI48*>p@F*6zJm*o2@^hx'
    '^M;s^vwj-Gz88<A*W>nag1ZQe8LYNmOWCVR@$v#qAz2N*P6pNfv%e!Gf~2U%4ejR>>G>_%BN9ru8`^5j=ay;`2|Y()TIoY?Xi10f'
    'Ysh^Zle3F^y&)YTmL3;TVl0xHU4W}qK!Q+61M3SswVfd@7yXIrNwtDei*Fbd3t&YCr8J$BbO=SXL_XSkgdF-uLmLI39Z_Qid3|Dd'
    'NN)urw?&is6)1Hl&feDKEUFR!)-'
    'I10j%Gy#DR(A`ES&?5qKA~(WsE(HA8<hj;Nxz!l2q>v!)l@kO>JcHf*qz5V9V7|`tW@T&Le)%?&{s!h)69i9Ezu515{O}PzKm=U#'
    'CFNa7d$(OB%*Pm#Qu!M;WA<ZdP!G*CMF~)d&ao4)muJi;(|JemzV+l$1a?UIT$NheneGB7PlzzFLA5B?q}=a<AM}qPK~wz;LkEQo'
    'NbvC?Z+Vq_&*1GdJVx%#_6NXsMf<M}qFHT=H2;KqRe6yLp%w%>ba-!z2CWqv2|@s^#2hMY5*pg}wAmxp-'
    'N;hu658enHlCD^>~T9!3PD)-'
    '+h<l>B0rZC_kBw7fyaiP>9B&5pDuaXDNAs+gp^X+>CoaS;jha9)lg(R5{P4`PJN=}57NsHDzbBngQy#Aou1c}LW$yFZ5pxD>S+*s'
    '^e08`=p&Cp?<G<bfr2urq1tQ|zj`w3pXzt5eF56VwUVj|t0Gq8zI+p&<}WEAyo?5qJL%F>CeXRitOB8AK7qALyUO6;I692q`V){3'
    '{KcfH?=kUFY%;jy^2eT43{b3Ms^!L@322I@0Xol%><y?e_%5zO1vy=o=zS0dmU_jE!ac`vgrLBs%zDlv9g6hfKMv5v~m-'
    'IxTz)Ig3C^*5AuA%T+!P<!101bc&|LGE*=K)gx#-'
    'p#4fOg;rzd9usYz;+8=mdv}@8MW3Eq$23BYFD&SLX;As`iJ$6p&_Tes0|<tSrwr>$5zSKhb_Y8Ym2mTBs-uPH9e$MesZn@7Eh8^9'
    '16R~c32am9w==*8rMD@Bv_)%>*SXs?7M&Z4nZ(NdkjFrzfYn0|2v?LjG1>DLRX3hj;abPHqQr}2oaHR^7$Qqcz5@5=>o<Q&?$=b4'
    '4bIraZE}4Ft6c|j3R8@kQ!s3jIQ2ND&Ok7c+A7sw-FH4iwzkQp){&n&H$SOh&Bw|4Y23BsAa}g?F;o4W?|)^s(IJ>oC@UDC0QZpz'
    '(&BD6oF&Al8sZ+kcKH0I)e_4!JKNq6RMJq1B+Sp=PD|UtHiwXESti6IzVE1N;R`Lm<ai@oLMUV!osE9u=TU+x(ODJBdlu<utzED0'
    'PH5piGGRu8dmVMWwwBym*m(PeC6YOReS6ZsJ^0yb?Gr@LqoLW}*gNmZ8^A={?3Wi!+{`uaEPihqnWzr6#?4$mKoQ9ti6QM%J9(EK'
    '^V`(BQ|t@1QmoabxG#E1mI21cWG?kK;!GK}+Ml9H9W(F3O?Y{%5?$-'
    'Xa*hrwObCv!C3KEmzD0sm>o~d4(Y~aFIkU5f^_e1*SnhFEV3!iyUWl{hwo6ONej*l>P`bqSuP#hg&_-'
    '=n#3Xy%ZPp#FJ4w96<(75f(}G53Sd)k2>f7kZ=>BE+ceVHz`ZbB<gcbBzZe>`V5~!YPWHB=2kgv!xFi?w)&5l^YOm`4QaX2*sUDI'
    'PuPot%uALbUvj3+9_5Eqbgz<NZGz`_Cr-z>7-*nhStb<$*&puLcn;M?-*RJ+qrK->;+;O>rMO-fdH>B>!&#I<MVug+i1i)Vb{(Y='
    'tnFjKX&|D?(sS`I@gui{>N@>#UfdGcM>XALzg$LQ(xwpdW6gyZeVL~`dXEe*03*qw)~3hI6NP`Wwc&YTv)eqRy-oAa_gQ-Wicsz8'
    'cmR;IfY_*^UfJ_ipJ!o>)iEAl`^F_|G&A3+d?8KGK&e25w<dlDb5+3M2{Hkz^%l(7Wh0&>^x^(sc2;I$}uv}+Zqx{X2P7Cm`YKhN'
    'AV1Si4E3UeT6INdPpmLIL@!57Wm1*}60oCex13ayXyA<cJ;S%3IUExq6AoKi^-`EDtQvZP-'
    '5UEzoD!_+Iq@;J1p)G9%YD?aK*A2F(A^&<wc8D4#NlDO=7XHZIk<Lw<r`c5dS>}=@5&N?aXcjm=X5p!A9p?)BH55XXpL`=!W$8*X'
    '>8>(*=>N<;xxlD$6zjJ$?<E-f&>#V8SIi47!ei9z5#J=-!Ed#}6G*(N}9ezV6>DXC1!G*2h%h!_~VuPY4>CH`YjH(S(O)^SK-XaW'
    'ZqqU278VBuDMO|`nSzzMZwF%x`ET&SrUYINUJHZ$!+PD}M_Mb(WbR}^rAGzpgZF(8zv%J8lOnn`l+``OPQv6P6uT)CUB+3mbif*r'
    'a8*mX{-TN)MTBo}ikrJit%Gnwtu9$>54sl*pP>YZki3{MU%Tf#&5eD9>-'
    'VJdfx`^s&=I}ZV_|D|HUS3y(8bzt#eEkTqGwk0rDj%AYTCtq5(2{6SP}BZU1=NHuOGV2qk<%n43lVPXH}fJCMh|+n@`5=XQUyVWg'
    'hWZbIe9S>zNPM(<Sz$WjpMB(GQLoHs@9e+_lq%%9W9)!nWGEZ;3>w;x?vhBvc4o+D`ezT<0YH5aF&q#V05NoJs0`ANKk{`f}KJg;'
    'StYRpt^8Ap&3df%8dp#bDdr`t-~8ic`Y)_NPVvm8&s(L*Vw?p>(^2<gLwy^1-'
    '!b9p~ltqP(QxI#4H>>=osZR)Pg2;y1*Ynv@Z}s`<yqIN&uJp;fY?FQ1kj*tEr+Y=wNH01xTR*Wzt4vBazdEFxoP>b&yKw(;yH__n'
    'UM?^P6X_t&^T_Urbq)Y%)U?vt<T^H%eI^#Jw1t>W8x(&FF*Rn4+S*F4*jBGSH$VIM5Iu%8p#2%9uj!E$FCv;$pY6L!&vYFKOCA`='
    '7L|TMp?F%z}#&%d!>%&upaO3PUjjMKN9uh4my3e1ob0F3cnFO1%O6jx5VQM<sg}iV^xL$y!*`{jQ<o24_~L2SWZLVGE!yP>Tw#o{'
    'gb+BilG+IynmBODjd*!b&;zh5dtOL6j+uL%yeD^jC?=t0Zp3f*T(dD6A&GE_rQD_9IN*2w8DBXL7E!(#&X5)0{Hw%)ap>f|P(ZHJ'
    '`nv1z?pWRLa`}4lO#Ua!FW+5H2EF+YBqxbZvs$JPB-hbvd$yEj2r=A?yL;hcQd<3;4pFc*EUQpn0Z8XUArxm(6F;@)oyIIx|xGji'
    'Xw`?V4)bmm-!H27NAIQZ1-tiOKUeHBy`Gj*hyFEFfb}G<xPUBH}8p?BzYcjHF7M=~mjUnB>BA)D$Enjxi-tT|r>HeWg#J%xOQ2DU'
    '8C2itn?4INb=ujVLHg0!_P9IIt~EV|f+UMAo#1M*}G*v=4;X*Mg^H39Nyh^px6e5UYif<^eatro&aVJZT}ES%ivIbEUo9Y(s#YnF'
    'FyNazjuaw!DC(I?Z)eF^9&*!1Ln3xuZH@?+Az%J5{0vB23#W<+dO)9^0Vy!(l3^ea9_y){xzV{H$DpK!T}Mzg0yBnYNVPyvgc|Ro'
    '4S{v|IAJUqMGmEP=2<q7!9CNEv%(`MT4jn>3f=rSH&w6t&by=#c;^1vLTq#bI=dWC<CH<a2em*kU*}bcz@Fv?#Po7^fbNc&*vdmI'
    '6-'
    '2j&J+)KxHk?d=!R<rl#<bl!ptfr*c76Bkc=o*wpx7Uk~%lzH*A=7Q%g8=xI6wjoYgieW&e&3lo_3j~<&|+6z;bQhnOxx|0~jb^gs'
    'aF_Fzv3LEm*Ya`A@(f;CVI;&TO6r(f;o`wllK-'
    '3y1@YJeYO(7T8z(^G)HCcOcB}Mxp6Vnk3HsFZ!{5$f2f!zCr*exYZ^u{B$#su0v3N}Rdy`EgPsS@=_9wq4lEIHHb{|76I>4p'
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

