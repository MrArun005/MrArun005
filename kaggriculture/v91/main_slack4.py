"""v9.1 slack-shift: v22 route, WHEAT+FERT sells up to 4 turns early.

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
    'rk<U2hyoa{Ma?J>P@ogOubqt~BQrjw>xF$%FHPSS;W(3>fE!wciZ?cS}c+(=#2J5s{TW<nHNh$oc51tnBK_$jHc_{`c9x|MKhK{`'
    '%{)fBM5u&wjl6@Zs6*AOG;|KYsbIfBWw*|N8RB-+uY^KmYnaU;g^(+4pa6c3(cBzxwXeUw*!N_x6XY>t~;T>%;fE-H)GNtigM)-'
    '|vs!`LNr)`SSn$_q(f)pI^L~z4OEF`u)4lFIMZ@+yDFHACBkp_Vu4X{doMlhk5<<Y`^>P@ot3g-'
    'rs!u{_f?y0j6I+9`fDSPR;UVP(R+hfAi_}$LWZ{u)h2B_WI4wpRe=r)18H;W15VF4C-)&$%l_eHMhw1)$858LCh=9-'
    'zOKlH}CW!v$+Qsi$6y$ni}`8;GYfgZn93NM!q-G-NH8+_~Dv&K6~d&S08sbr<ecJ7vDY}=GU(jEIzryWcm-+dVO_o-'
    '>)BRw(n%Fhl?IQhwde5T4({GF@YzYewVN5$)ybYB3IHZ{qVyT3m;r)+``OV4=!Z7>--'
    '9aVJAM+YR+gwnA<`z?EG<R7<T$k)3V^Q&Gv*dOAQ9zo!-'
    '1<b3%KiMilS+e1_mvvklR!(60THIkjg0WKLc^_66=YviR&99P&2V+4JzB!Y_m4<Nem&@muqK|7nb?yb|EI9?qA)=Sl9a`WCWtT(9'
    '3>U+-Rj{P|D2n~!g=-'
    '~Q|ABe?#{AKriJTh`@<`R3;RkLSBvKkTmm9!F2+F%72|_9bZ>Ts8gjlfA9kDh)cHe<KWg`@L5kmQYydb=6TFR0+Dump6qW0|%mz5'
    'Cj3FtIa*^=n|6{%DtGhgCAcEuK)ZXE8YVuXmRPzI2sm=O3*oad?aW!Cg)wW8q1hue5EV{tw)wh3Lx7Dl85c%KGS9r7<_)S$&I+JE'
    'o_t|!tEZ({QMMH;_&M3D`y$VKeR>I$w$OQ&S9T?Af|a9-'
    '4JbH&SPKk+t0$EogM$T{_%fn9sg+{unqIe;_+Ng58wZ)3}cg1AH3XbH1bi@J%?8=-(t{{+^KpgWX%~8znC#`7)g%Gr*GFUkL--'
    '*3G?_J(bY-'
    '|YVt8v4YF2;ls{p~S!9_Z<twKonz~1nuUqGVKn7_>&nd;@gFHR}zCHGkp1R2(*WjDQ+(*npLwY*KSv>#ynAiSxfsP<!Qw=iG6HZ$'
    'Ma*^;@dn1tJNBv?k2%~_G9~~>9$${(Eo1V!L)kBV;!xS6sG^XLr=Liy!NhYL2iT*^gFodo;$ig0q8i(PpN`B?=_V-se|Kd!4Bf{n'
    'PQ4*cM$)tN2Z*(~fIn11Wkp7J3G#Q%8l|`02`k4sbhzQH%g829ce(qpTIkFbhD8z^}zws#xlYbt)gcngJk|#efkvYh=ie%25CjM~'
    'gBUeGw3-4~>p~03fr#Xk|X76@Kra!*Vko6~vt{Gg2Ou%fRZ{4%B9^S4v*I`od8nc;-'
    'oS4GA*{u|<vo`rE*#Gc2yf``n9Zh$WmX3w+J;LJWcV8K@E(6eo2iDz>6^4oywJ>lg6iX0^!pMu{Z1IaR^jjDz%DYNKEv!!6$XOMd'
    'G=l`z9Nv@*mWUz4@khiMwDIkWJ+RD0A1o96$mK$i%Vt5K<-950J9D&yC-'
    '7S6DYp!pvX!DYM0F)5(ai6YS(BR0vp`lUisq65TVnoE@>GF;i5GX-'
    'X<BQn#*zdA^wx7zpi`*#u#I@BtXVf0%!1vqA*;l|4nAh()P_c135{+12>o(^s*FX~HA|HlEBVszd#0CPL^UHCKCfmN^0)cf>_WpO'
    '-oL-TQ;-Q^iA(zgdVTfoO;!Cy3z~trO?1Y?XB^}3{A!lT{P6MSYX9Bt=H@S-'
    '|9Yt%1&H`dn#~+cKdOosCj`XFLm?FdD(U0I_(J%@lTDf%qj+Ejt2DVRdiP<ZhwR+R$IfxQPFF8hVaf1Nd{8VN$zgJBmb(t}Y?Iq<'
    '!F7fOiTEhfQ3;_Q|Dfey^6+4}hWe4MNFzmSbTY2|o|?_7d)P*V7%N|$Zr6%yS_8k({PwW$hgUP^fsmCnd3hIu-'
    'T=!>@zx&XhtfI+VYtK#kX`ZfW@PENBTGLS!{n42SsYHobA=0ew0bTwaSZ%&5^s3N9(nXIo=VRe$M&6!(AvOChQ#-'
    'bV%}NcRv%_gVxFh6TX?A#W9(cKx0-'
    'BB*#aHHOvWtp0$20Ggn8`*w2wh{y&T}Pa_QBh5OC{8t;Y|9;EdsjoepP+R?oGk&_tdSs@p`fDZCUnhL^VnwIIIeVPf!b-'
    '7(TvZmfhadYB3OWSJ3bI|EQ{ojr?o^CK1<Yv-'
    'tQPk?bAas)KE^0^9)lPTn+F?ygw8ZQ7O+b-=Q><lfC5S68{GMdjThYE@g5b!FQL9?d^yvykcZAT-Ch`iWobeJsxdkUs9hV;r%X?3'
    'K06FhGMiZ^tW>ESTtqsrv%`T;s;?M62v-n0|7n=tD?kO+i6Oh^W-'
    '!lBHwSE<9=Rt{YNz1@;WrMkhmTA)52Cpm`h)__7TYogaj83f<y5ac@hC31_Tl17eL3;D=`<^UW78JU#vpUaTaD<tk64dw1CQE2+Z'
    '+v`7LB3|(D=pP`4TM{wKS)zV(+hJP{9OPN}d>*l(-4yv~ua~Hw%Mo<&BF?+7s;I)+LKRjWsKVW=5&9<-'
    '6dK18=D%BbzMnRf2!mK3IvC5CpH_qliJ|_1<#{TUUwcSW>rh6RhnxK3(8|ICr4^5|DU|Cj&?@IEpCtm*V6R+_g0K?Bda&%*LNMxB'
    'HX8>G<Z~~mA2gvSp%qus?>e`lc+}Gq?50C_2`)k;kh~bz4rYj|b;fTxN8`JD=ilc|>6#qG)>&N(_cM`PQE*Y^bXpj25C`B&oUA*}'
    'qHE3JQF%d^TKNW9vi33MVbVE<G^6}(mzTTh8#5~lAJ<iTggfPt2lxbS*48-'
    '6PyM?oIW@fA1pmJ<W9=xL;`dcRyzVfC5A%0RbJ58W{4ge#)L%%bOBKu_N&6OZ|44P{E+u6j-bVkU6&9oQl(I_H!L-'
    'OR&dT5>dj^JKkZS;Crb^ClrIMs`_XsjS@Rl6U%FE1d7Sv<QBhEw;{&(}H;pvo(l<mT0&))QLe5t!203-'
    'O4>*w1M);jhW;^q)8?BK3n-VT*5;_VLZHkhbua+t*_7`H0P><4?~DD~Qr?ZPh+Zw!%CddEl~8IvKv(-'
    'Ofe9Z3;g7z_`OG9yl34M$*{7KIVP$)*+znq-6j-oSWPb{j|LhG-zi--'
    '!a6=D6A|4js)|=$Sa3ZrsZw+kVXpZ{mFGE79y|m^{1f{{Jv>lJCZ|efY0iWvD1D^uu#9yy{mSEL1puZ{f}JfjR@dQ2w4gFxfdYkT'
    'Iw^;05Q=C-'
    '9SYtj^+y60w$A>28I>gkv+}jE)wLOH}F65)4tLD=aimvjF6HLM%eijmN<+j>;g@5_f_I$dktgE6;wY)g&sufQ!S{n}osDITzs)RG'
    'lF>wV5pDj7eyKtd6-G-H=gSqqrK2j^Eqs?%AT7lO8nPm`5&+&+ms^ro$>RVL@Ncu9+AVlx%-'
    '}cgQyOBLnS}!U`+JJLn9_cGd=Pb|b?mDaM&^CDU6&_YU-'
    'Rt57SKeK(P%7h)^`QFN&S$f{#tX6}_Oc%i`+7Rk!HJy?Z|@JPz=G8wiJt)r@J7wB1RD-CKrQ00`w5M0PYmRKGk7|KOTa7(dhbySK'
    '!u*(b8E>4A%aF?MO7g<lN>_jh88@JMYT48A8+*>le%A<wmi(rB8k%dBBP8FdQZUaq#lQQfkMi6oYa*5Cpk{4Rf&nODZJIW^{l++m'
    '0lbuE`x*d2%6<CTBJ5LbX;$Ef{Hf>Dru;gRpJ0%yIVf#^HQ;7hGO33qqL)H|g==O4H-'
    'h$jgn3gJd@=|lj7pCWxskpSb5Ya;sBF@Ql3KJD;1TO}&0Ejv`ps~B!))i+|fO0XqB7!U@gTfLhULEEV#5DAvhHQb1eRPg43S`j{6'
    'R^rolu<U-4+Q8s5kWeK7AnunvrNiq{^1<CpIoJhGte3!rR|t_kbO{9mZu4b-;R)UIYlw&lI9H;8+(-y^|1yC)vX-'
    '15Y;ghUZJ+DLmS4*RtQQ-'
    '?Y=BisXZ&r?C@v|%SzcTc+p9BLQ5c#5Jq>0WMK|Zp_Ix40m+so#|~RZ%MYEUZ>Tyveh0R<1_@Z6>OG|!43UXy)GQsImY|Oa5r8||'
    '_I3$ZWlBZrP3znElod!6<wyzWOU#gL>T6jH;Khd1i;DRagX&E=s9uQ;78`YVN}+U#{neq$%8D?$m32sPjB?~nqfyriMrEvf!QOma'
    '$twk(No<|$^Od?zf%ph=t2kLPv`V_1OnTnbO#_J>jJ}coGa>P`DNeF+Rfs}%i^6;ith>t2llzgIBN2XIk7<ZV3U*GIaDc`ktuY2f'
    'H?!I`NqM=v;V>=}y`fX1R@Q5$s(!(ROZVnZF&IJ*?AFy{6;paQt)#_PW9La(#tj9XLu0e}I&n+kEYvFuGYa(9W3|bU;-'
    'mLbAXsaor5%;jddZ(FiyQ>cIn(3FV{4IOOGnhLle>L|Dl<n?w_?_F35nOWs6o@B-'
    '+GeXIgOc?Qi@?+T^gFci%Kv|tl>0TJ4Xst%G(uswTpQ%Jxvsgxtt>xN-'
    'C*ZS8hA7a`;eZt(~m=fu$SLeA$de(5;98L%KX{EH@I|juhT#N7<$Vk4wLZj6@8UM_r5%#39OtLI%sBE^S#Uj>kCbba`ucGhw0*){'
    '<NfNE#$sTXoVdn|+>?bZHEpxV|imfQHs2?JJOR<O&yU=>;(m_$<u1>|f8zYfEjzYJciRI^?T#A|m9<tqHl~Wq3@`&ylOm77D12eB'
    'mD|4|k4?oROTXa(06$bY<~yHpFQI;byg(5`O0&cvEhWN>Z|QdYm+(lQtunl3qVyLm-DL7k@reYSK9sGqCi`S<L*b#+GpRVVIRz%6'
    '9fCP@Fe0N+t_Wl5z~ZTn4pdZc^{LM7}lFKNNNprer9YoVTW6Sw_lBA=$qy=e$gkvX<w~7;VS=J*vCOX?a*lFW(R0eMd?NSy`x?nv'
    'If3`FOqZZnh>-`{2|04?7pTr%Qc?;4&a?s8~{LLUizk2$;!oPhMZ+u}W<=8Nkq$904(T;)8ur7RikZ0E5-'
    'icwpMTXfyXDs4tt>KaX&o8><6Gby7zu+vhE%Uag-()%03zo1%Yp+tdeUd)u15UrSZY=W7JRz=`9o;1AO|+8;0CX&-'
    '%V^LR7?1T&#Cqb|RBBt@`nf;tzDi(p!rXFQ(D&Rq-wduUE7Y238;h3hxb4xW$s;nVYg{^5=8dE|b>x>GRl$}Gth@7a3M6YXoE)oT'
    'o;-'
    'R(1d1Z=?A@Wh9XzU#Zug<ZLg${k@ym8*JAizOv2fk&?NC6nlF=sINAaYvM5LfJm?0{l(|J&mhb1?+2p@6Q0y9AGZ=z;Y`fLi7<fL'
    'yPaxLiRUseIQgARMVGq0mQNh2jXK;qrzbasK;oi8o;vw(eG$!=U=UKqg9trk*tNIChCW%#(NUoghUd(#GCaZf;*p#gcNK}h);s0G'
    'Z|AK^>Z4HaR3ZUP>NL}zs2(JZ9DB`{ac`&(3e4iV_{lJ7~E^jjK#PD;JiRM8mU#2sje2KlaO;FqZITKM-r-'
    'R)>xG>>d#9P;oa!;aIww`(I1Vh>!biJG*dv*=8$ne3O9`pgBG#mI2@1CZPF|@FO*5Ze_AD{{@IvR;^+;1tJW+WKypNjp5TvaECM`'
    '^)!Em5pxOfmPasPC*8Mi$P#GNqpIw|Kks=kb+J=YhY{!)5R8XI?xC^?lOyn84F1#2Vj@2|!vTNS(jy%&VyGSiNZ*^5wXVRb=U_Er'
    'fuu!JU>F9FrE=TPop~%@~j3>P4Oa%lM!SG@59Dw_SnSCdjFQXxEwaZ40)T2T>$aADMv4}1sOr7Hvr=sv)l{9g5vCH@dIAb-'
    '=s8+#QDsa?6Zi?&(Ep<Og`{>X~(1;RinNY#Xle%?_)#CmN2E!0e!B%G$4glGqJZ+`Vw!D;0qzxDcLL!PDMyAKa^HMwtOcW;^V~Sr'
    '(Ge3}L;_SVuj+I3x-Q6>-dS!zYV#U^RTF~ur;1<Ng{eYyjNKlZZ_UqGtA!7b8p!IHXcuuMqmRS_&J4Eml`zFfIg}fhcODwdm<A-'
    '^MLGx0Dx;(i)&rxAZyknfK2CVasrR@8Z-'
    'YQZRn!I7s#*DR_Uu|!@5U(7xV0BbvG0JrT@M6`aP*{HD(G%(e%RP~zQQT45j?Xdw<g0XrUPKhQuh*j2IM%f;3dcQ|hP9(fS#&R_E'
    'yQ~8(8d=~;OLNI+=AD-qE4i7Y2Ik!@XGhP0Fl}*-'
    'C{!8bB|wjZFVj*DKOC4(7A7<rSxlOz~%x1h#{L(swVD$YgTTHLA06Vzy^Efk58?s4`FnJl*m*0S)ds|-'
    'L|wjJt+c#g?SOf=^WVG_O^q#71luKOUtxrs<Gw}LM-=Hjd(Qz)R>@-'
    'Lq6*xBTPuwrY<(s@C=FG%G`wr{U|PBN6noop{tAYFl)e1j$@8Val%U(OU~(;D*H}ZTbYqm2PyMzlvcT%RgEJRiOJfzYDYojwNwp-'
    'pc?%9#=@Pz8DFbubj@Ix#IX<!Y5QSo8lduN^AM$iXf=owvS+3sI~4stXWpuZgsq6YE2P<^w2O1h##@1MW=m`TN(kc$>ls-'
    'x)tcfc%GVos+e-'
    '<di3YgRteccSyO9M%1h7P7&?N^CXlp?ib*dRHq3NQCnx$KfJ;TJwoLWP<)F{`PDlq&Q*!T70jHvEF!}%OyM>H|m%Z1p6tIOEqA6d'
    'PrE(^YXOsF#@l+k*}ON*n&2$0~Xbzpc^w$|XIE*B;;xSPD@a??cuU822FF0_q=oC=8f*(NOpDu@;sa_u3ECrO@+Hpw2JyzKd?1DM'
    'cX5`7J7p2QNEL#XBp*U90j4|%!N^oA?dSEsvm9XaLzad<k2Ku&(gs`rq!(=E(_o)0NqZ>Q>JGcd8FZa><Tiuf^uMM;SlSv>$hH8*'
    '_<`i&t5D;GhJzb8fIvLINJ9vxD-'
    ')&=I31xM4#CAA7g+qt3`tI;J9ovxlh@7>dJR!aNL3SD6}PrfW2D^j`qLj9joaERO{nYhwUqfg#|hy*g=IKY2){3*-'
    'YShzL%5aCgDIx}q(!R_|C5(+}A2bYKJVr)$$HhutAm6hf=Y_9VnwbmTcgk}b0>5%R1kWfS%5s73^0dMrb!4PTEvhY6MdLE;*7j7$'
    'BPV&zMe<)i!IL?o0)fHU<p_K8ClLNF4c53S%=4+PoW|3M!U2NY0i>);sL4CEhj!;PfRJlKK7VG+{u~-'
    'Ldt=CePt5T%AKx;@=L9bIjwSV^ag+y=?mA#>jej+`;MLR`88FoWkjrrVCts<f4C`2fI=nakO@M#UXk7IInY_GSaBb3nN5=x9NQnL'
    '$CvkFHL@@HUufn2sT#O0!oxSmui7q#esL7@OvQ&7svi&6&$IzVPEQEupmDD%d=dGLM`HB6A#EC!4!Jz_wY9HG)9YNIAKI8e$~ob5'
    'qTvltVPV{!)q3LxwcsnB0x+h~+cq};HPv7>TS?_t79p9o3K7`(D81UH9LXDwGe=`(VXRkRu?@P(aCRhdB<9?Kyu7>E9_yMF&}PU4'
    'O?aYKlas~pAxm#X+8#|%X6L+N~tihYAa1p4S?=H#Er+tPeCE4a$*gxp<XlS%?19I=7en8Tw<B9uZHg^MpECJe>2WY(|TD#9lQo2^'
    '_0GK002;_)oU5w!(vA!lx5Zf05q^P44ZZhj-^-'
    'pZwurSwD6ptPHXdC?32iak8iH=im~^P;B;IX7jIs%iRWH)D0EL|Ht@*O;1q#g$5696>vwMZ&0p6q5!Xk&<W5==v!aGiHA=H9XSb#'
    'N~jYS--rkw_?$TXJr|5v~npnBhhYUEfQkn%jsS*C@HBk8cCWW4E>p8W8ML^>cTI?>N93)E@?wMVd!+nQKqrJm<|{wEpiHIRTuH)t'
    '=rg?^5X>Y0QNHB*h++BHS{yYooS7|RQTcEsYAS4eajSySZW4Qgy0AIXK}3(^U*-'
    '+M>%tfpb~a@J)yI6^#?~XmfUaPj_zz16yG^Q5iXI7W@n)+pJv{SDp8C+BeH}aHv_@fSiXM-fWNHCnK~eK@Wm)e7CQ-'
    '<u*ilf3qV+HZY`=}ehdh7Wc}M#=BLX0q1^gCLrBq-'
    '>bWU*^@KH}XFaPWb7kf%o8`0((lki#ud{j1duBasB{BW;c_VgwaenN0DScBbRn;YZsuMy7A>$4x80wue1TRG|OC{MI{7_VY&D*Jt'
    '7L#}QQQl=nq3N`YywDC@Q6eP}O{rVX03(#1rx1P?twCO;Zc}q~b|~f&D<?!A@Q?yl4?7@iQRc+tp0~)l@w^HLJANxl#7M?k&O(nN'
    'y0qjg@ZNm$_MejzHkDn2Gd6?8T(iOI%z>Q36jJ8&3!5fRJ&x%x5CEjMO7%zggU^s#+vHR0Fi)MGpH#5s<K*Nu?pkt~JKp`6DfZ6q'
    'e`U7OCYaGE$2xF?*dCc6E$((BU&4T@VeZjmhtFSHEwM7Q-'
    '1dgxjfQw6;eZabxEbqX19_Ka?mA)u_cmPGS^}9UMBtDkTvjM=8f}hk?Vwk$hDoYKmsP0!S)~89cJhAMyoIC6gi#HSeAIUvrZ9gVY'
    'uw8h2vmDT^bPwEwAI>I{5+3}W_xSzyr*se6m7FNFPiw7Yu;P@(Nr=~EozOQxqh00k#+|d(pI&Td)YB-'
    'xuv$+Y+_$1xMDpp#e1l`5A~iMTOszRSIm<><h?Cp<c?LjK4#vBn=tlRJ-gP6rM)G0iow|3&^=CGe&d8C#yaiL(Zr+#JF};V^_?Pb'
    'c-6usC3wCNf6J|u#)Ur-6H2I3Vt1b|D^<`z9cvl*Tqd888`tgP9W6Y`$izjOby96XJTolR!-4sIY-F_bk{w+0ViKMS3*%GR$}qae'
    'yol?F5kyX=5waFp76xjmu^AKVbnxSZsS)^^ZghGoE&cv5!#L(WQH_PTT9kv<HLZfA^2)&y1%EB_;MhM~6g+7XOVDM=>-'
    'KFab*kxEC&oQ&!kTET@D!CBEs3i+TDLrKzQ}86eEreAkk&A>xU+vs5<cJ-hj|aBs*1bs$#;>1<k|UxSnC5Nag3&3Z;S;sP&nR>j3'
    'f8nl5UmtQhlA)GADG^h+1Dh9nF9Z?W@_Lcd9lS2PDTXZGjZGtbo%?!Oyj#?sITKAvBDzwIUZ(RE`;9_7MzWm=&t!&4=irvM2G;nj'
    'JmuV52D$L0L-x86fBCUaw+o3SN<tN4r+3s@ohyZqt)j=JOOi18Wj!tS|?HX44yno&TdXJ@{hYzrgO&0;hp)7lqnKT8`#-'
    'jOk&x+J2{#NF@p62fGt>NWIvboQy6-T>-wCdX-xqj}}#CCEzfv3m$~~{R(cYqcI4{u#>pz#klr)XHZRnf9@To`c5dfEUcc@{Dtj_'
    '5)k0bHJ{*6kB_|vUyy?%rt0D?J0+qGRlW+Pp+#|ACdRzqX^qjFx}f9nGDaw2vPz6P0^Yp39RX(<yVcTghrdvs*rnA#$XQjvX{`{<'
    'm!0jVF{2LZ&CPO*k`7dAQs#-'
    'GsW}~i_NnMDIiifrBtihU2<+P|gg0*2F|?Sn{+46QJ{{okam7j(Bg6h)^hs9|Q}W5vUn|n1wMl14(9oO*Bo$=x>*$nwxv!VE9VPU'
    'H_(~=DOj_Mz`85IO<wFD$-'
    'Rzw1kf11SZ_d^j5z8dhvd(%X#rjgTFA0cP3IikZz*`X+q6?$$TMpmT!ufQjt031X%KheRLO7gZ7q3wf(VV}EC5eSjLxZxK_LnNaJ'
    'A42tif)OhCMh|Ha9h7|9HB6J(6f~n%;}IS;5j5GN@~u@V~y}Fb=M@H9B4O=ZzYl1h0;^C-'
    'gLQNjN$2M;bh$$UDO6oF{aRsW0}DEl6b9<kxz}6+^mJYgyaXKJq>HR$iGDb74#IO36YmEthu@!6ZZ%o35-'
    'vwi{%sMVa~2hO6<^@b0uFkufrovd5$vENL<QIyu53TPbw$~Xf)*D>23+8!CZ&kDc))0cNnMz*azLDoc>$TM7&4*GQjOCgxkJ|3EV'
    'w+?aQa!Tk8Bg(NSg4!B#*EkU|5>q>ai(LZ=I1v}I`Opo!9_Hy{?|H))CHC(l~LCOx;ln7Syr$qZ%8mKhM<C}ngI_hMkEAI^5Pqz{'
    '5)ifQr^V6(r;K%<giLqpsrJ935MV+ysmprz^wk=@S@jpnevq;&`Fg3_{XIiyE03ocA7%TfsZv5~eb48;(n!+6~jR*5*U5UL`$FgL'
    '(U@&@obvMl=?mF!t4M(C#`Yhg|IJHPKn6h1z$a4FNRB7elNrO}tJMI%?w$WSDb-BM&aF5a;%2q{Ir#R@<6g}V*Sj4;vx14Wp%!<L'
    'muzDn*#tl9CA0>11H6ofp2AJDwMEBg_ia0JdsEWUlEE7GL$Ii>EIedgN)N4F}oz$#d%RJ{i@T(o)RVzUlae4w*D31E4-'
    'IGTm6D%+>CEA4cLF-to=e0)yU@!`RKj+r`Lk_u?&X2r|mk5Q;?+(u~u+0)-OKedS2HPyE-MJg=}`dpx-'
    'T1?53lILw|q_)`|9d#L1K*pRX_snNRv{PKk%13}0Nrg01qO@Bv$wld?DM&~fV=AJ$dcb%COP>&#Q+^o77ai;?zRyD5^hO|VL;+zE'
    'Hrl<yfo*9D%PY7h@})H_8YnfP`#=a<Eoe&Cxf<w7Pf6(pC0Zz59&jUUI$SNw6BfdrMQBJhSK7<HHUzktIS}h1$AFH_tqI`a)ew+X'
    'r{%7y_fSCZoJGTP<>0!bLSWxH5I1%TMh$G3wqeR`(bQYq!cz?iO-'
    'PU;jzzoktYnu{WdfOWl-{z*YJH`{pEa3*9PM_x`KVP6l;8RMcBt1jX%NMW(cz>iKFC^UBTVQ-FcCIWxa@Fp4o?CwjDy)0`w>zN$@'
    'd1Mk@{k6&2C_?a02I|15QKEZ#J!^n3C#W`*a6oUCa20ieRx2mYU*5Qu3@GZRY71XARZIL#?;Lz8>P4jpG!LE*KvdZJN$NWA^Gf%j'
    'qoPLIkG$qsyiT@kVVYDs^Xb<}E@P*Y{VS^hwl1RP~f9g#3})h<j1=-'
    '+FXQB`lb3lqR#&kb({2Qf=B5F(+w~RW69&)iL}GvR1os!Pph1NLgcYg}4B(mgmsXN{donj^Y(8lS}iy@v!~GK04N&B@@jg`g6Ugk'
    '%9d_FNFy#xBm}iAL_O'
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

