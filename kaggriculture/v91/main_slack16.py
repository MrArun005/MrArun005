"""v9.1 slack-shift: v22 route, WHEAT+FERT sells up to 16 turns early.

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
    'rk<U5^_{a{Ma`J>P@)F*B0iW+k3ixLIkTk0Z{D!D0cQVZb;)to>&AzgybT44dr8jEJmkjwJ6JheNWfGOMdABO@b!{+}oR_Umu|`1'
    '@~9{^`4)pZs+F?%k8yKYjP)-+%qjfBmmdZ+-gXAHV+gAAkSvPk;UV<cC*pcb`6?zxw{e-+sA%{p!c-n<pQC>)j8#-'
    'A^B1tik_YyxAZ9=iP4i^3(hKA9mO8Kfbt{{pZKs&70RBU#!-*xBvU6?~dp4>cw9^{B-=ghk5<{WWRg&{%(Y?-'
    '@JYQ!`;h!15CeuJmkBtotov-pniJ$=H-'
    'VM@24XM!}|WitDBd<e7w&44|f)tj%hLyGN{89CLcZ?)!ZUC*DrSW1~IQZ|3A6dy?Lh>naw@8So}G1(bTvHhkrE0>xrLEjeKvWJI6'
    'N}_~Dv&YxZs}UBBPGJ-'
    'z&&KdtTKVSfHf!QzuEOs4;Etryq#_Wk_9X8TU&dbsG}bLd`@riB~`jR{uL>36wLPcCKH7cC{t(homevG8FDja!&4*TWJrm+SlrhG'
    '8dbsMVa&hA_8<V%YiP)G+MyP1CaAvd#8{GfNEy{yV*S%jSgkN{uMq_xTLLt7aRbSD{_|Cv$4e{>hxYdh83_Z)EY=H#p>Nva{#mLx'
    'o=k$H)7vz2mp$`~H_PuCgb<Z#|qZzvW5puKOI>Ij$FPZf<rj-v9FF-'
    'P`xCZeIP%=_9!Q%kSQN=yU6G!+iPn%}?jMTi@+&evhLk^O%Oy3$LZk?-#ls!~MIf;dj^8yTVqy>YH8jh9h2LU>g#zps%&Y+e-'
    'LJ;kJLAfni{#bgMeJTJu7spcsTfifi`h5|b#h;bQY=*zv`n|K~?}@vd6c@2aC=!MF@X65}I5-k6;DkvB|}EZ`H%6r%a1uz28-'
    'IqWd*@xnA=nEd}_p23#VHqj)K?mXQGvpc-'
    'H`%3dAzqwhmbAX7E^v*fI<X1oCDvUF9!d)#ljz2DShD*&3*IWN^y|oV4^q9R3^VchN3Bp5|nv|Yi3qQSu5s)((9KvjbLub>KeM+t'
    'kY9V)=<a<Xhk9;x9D0I0(3<k;J`1IfP%Ol&Pc|tyd8zV`k&#zvcx_t&9C!o=b=XO`pU7bL)ac#@xoBnf9@p!V4Ag%LV{L#!X@GN-'
    'T5q(h>+lU+aH@}<~&lW%Cwg0$4;R0p?J_#Ap^K4r@agnfIdn1SAP+210RN@3i7<CS4m5|`Tfz!B~xlMEO<nRRH;a|dR&tYFQ`3c1'
    'kpT&e{70E&n!s-IYPdVOtlw8E&-#=Wx{i`$mjR<7l$0Bt8CYSDEywT-wP(Ql?1_{t;PLrXjY*}Qvqo0Yef{3zAE{KnG;O7qZlp|F'
    '!!9k2TTQ}q)Fy?u9^XMhKh%%8pg@LKeK@L)+bLK?xhf5zV6*Rrz?zUZ(lbXYXt9NT7Gauhm$kG!BYsM8K3ou)_j_x^G5C5(#q{F1'
    '(HD)sv`5%ROv)d-'
    '}vo`rE^#1VZyEqD5kEXjx3&rjMZd%v1f_GZ^v{yI^my0a!eylK5<kZ5zrBEtC6bd6RQnAG^#$ak;s3_Me4YlB%x{<S*Gie4109i?'
    '6&<%@Qr%a~OMm>-guP_5csG|@usXz8rf3X9)x#)v#f*-'
    'kD2$tC_2*x}H0y6}=z~4nr&GUdQz4jy1tecO_WfA+ONSRB!8^{i6q3T(gj>wTq6CEudtMCwk1U)Zr3M2&e&a}}km7nSchgtADHe{'
    'U~D4bCW+{><09Gc}=NbQx6(5r=5Ys;~cT)blCjppBcDQT3lZDq>&g=KSZwQ2IYf-!4fD0IaO4KsQ3=H^bzCWK5b?UU=x_3M`-'
    'Iy}OBVVDoZccK#`UTelt{P`?*`tJSP>;3n;w{QRU@vmp<M9{&8NY<oT)xk8VIO;&X<Aj(vdBml{M%tK*s{%c7=S04?A&CB*To(QJ'
    'VWfxL<H^T*!-CXzv7StZ^-'
    '4GpaoFK1v&?#s8=TyPm6$fa^JdCLO2%+dI3TbGOk*DGu|zEnwDHLZ@|8Xte=mtNI0MJZTBjQ;UqqwH{)5{NuV$<UA-'
    'm~BIF>JAK_=cVgClWRyWsi|*$VI0BaYkJ6$+EHWMoA+V9${kw<Gz;#I5+{Bqs2V3>RX=lRjsUZ8jN;wM~>vhS#=Y$XOUwA7)NDo+'
    'qwbSfm$YTv`%En%qg*0v)1D#w_y!RP(}wC+&odk3mhn9AKYvS=FQPY3oLO$0c&X^W70L9nRIPo@!5)iS#B^jfrMccqwiS&u$GOL4'
    '47}#Nc7IW2DdB5D;JVFcbF4GXK?H3_y`}_AJ`X4@hvVoukfI0*sK*LO_EnpOw%!nf6N>wFVlau>&BDcIhR;PQU`aP;rHog?w6KXR'
    'x@M05{1Dnpb+jsGOeAb~HMOsEVCNhdB<gr(oh@NTv)`R7XlB!Sf~{Z^MN$JshU&Q<;`sKS1Yv+~{V+n|7il6Xx#+(tL0Y6S@GaT_'
    '`i?Rid!AmBS@~{@s!#rJBIF4xm0BCk2J>)_@!?>z&s}83f<y5ac>_mC`<HK1MdLW&Jv8_TeDN$RyZ)E-^~4kSy<LD0f$hLen2#-'
    'TVbp;(~`q{{VAJC6HO1@ryRM9k%7bL7xB4=Mfv)O*)VEafy1h96<+HaVC3JMHSW-'
    's<7%n74BY*5HX=_&p4Ja|J}m#{j^y`7{vO}!C3X}X|1P_s_7qCo;gCft%tO&4rPQnu*okDc@`cht$378p<HEwyqtSJOU<RhUb*%J'
    'VI_+7U_q~iU|5f}5ke)2GuW4A8Kc4p3NA6U6qM|@PE9DD0rjl6xl+8$7s=yG%Nv&vW>Bkj_-'
    '{I3<J*4cZvahsoE+WOsZI+wF_D&{utb$(Ym?q%5H#QdnygJur~jJ>zp~?-'
    'R*1w8ZqOh*%Q*9R?99WwW9x2VFu7e`8>`>o+a>hZ`iFV(HQM&#tF>)gE2|n|;dF$Tc6w2T3O2#}7bb2HWro)3d<d?9nA{;r0cI$d'
    'mgXX{#9>T~wlF+8Rn&_R5L)Q`bp<Mf(4hBdO~s&FQQ&tl7jo-D+-'
    '!2kV?YQw7N|c}vX8cNgKQJLNyeD~NkP$bA2h&*Mr4fyUTD_KWn*I7V0m$tL{RBEK%htPC3mTA?dng4027pPn40cX6yp5`ZUUIeJ4'
    '$jkZXS~44>qaM0XlkJ_$8u{A-;+{MzLpA4jBeJ`D9@5ut9LkMEzr6)R-`X2TchTr>_cOHNV3+!wO@FlPxWn2uUpe-sgCJcs65iLv'
    'N4+{6tVqy&Z(m3vMQG@jA<7rhliq;ds@5PDXFkxCVLwjgV*4-S-c3Ci!(dQTT2$Q&Kyqs5p$p@mGE&P<~mz9-'
    '=VBYT^97e>P7Csv`74`FpBEv^m8Sg!pApH^EEGqfg-Hz*w!w5v^mrQ76pgBXP;avB_~tN(;^<68LCw$)#$IJpB#ob;CpkIfD^95d'
    '@@Jvf#=s$7MzC1YM9Pj}2CyeY6XNv9~Dogz8YB-'
    '`G+hfqBgw<{}p=IUun|Dw3u|Q8?MG%(}PYoN>!pl{eN)zqicY<489gJ?OfToV}iNwGFFUh6SxTQD|a1P*MK*zvEz=S{rqAlgze4!'
    'J|qw5;~5ut+N5m-MCO`z8y>#y}laI*R2|}T#Md8w_vCMp>(NC$tt#B25r<!fW&@>+T|^7R<I*HDl*JY28qgI-'
    'Ua#>+xUVa6I8M#Q4@!4VX5O0s-j#61#f+ephtxW0}EW;4wYL8_XwI>krl;iSoDgw#2#WxyZN-jxWTz!WU7@%CC!~+!S}L-'
    'U=^IOsx_faO0%2HR7fSrMMX!bn`NTQLfTO9>?qZcFj!**ZfL!1^^)F!2T_5-II;c&pDk`~O4-'
    '!LUrFmRvYCFb<>EGM+e$3mq@xOV1$Bc^ZVtH+uz^Qf)K(&rx%p~unxE;co>!*k)8bM{4`q;XmZno0sn|Ror!z*7eMI;h(9K<K>q<'
    'B(TDTa=5MhdwL1AeYuRe5)kcJ-dkdBa%lX?kg#F2>ASLGD0hjH&BXq>1nE#+U~q)o(_OuD9H+I$_LMaoHOCK{9hqHurRjwu(}=UB'
    'yoO(6Mpq_>V<nVWZUY;1T!M9v!2SM~UXh?}A43-xWS+lojIrOa|)=c&{ll;&4>0ETs{>~6j2;5uOgkT3`1vqL&Fho?-'
    '+%7O4>OFv|XWTWM0hSgUkg_>j`YdPc5#vK9qvwZ6yo=%M)r9;aUyI5isF;yb<e)0`=%E%+?aij|K873w+b*C(b%3|B-'
    'MTL8cf$F9lsIJ7ehK-s#rSP=GeCkkOWt9`%+#3>xqEvI!XjEUpFp2dU*qe_S*;C*-!u(`EcU3<HdLn39#R-'
    'KWFX;*~=}}O4&K(Das+bMqN91oN%$GLZNj9zuyT)!qn2&*VJ=uBMK5`==LW1it4N*kF%NBzE&^V+)#(?x@R-'
    'h*7FPFC>Mi!#CdTP{4Q*pIYnhlpxWXT>iR`r>;)9Dl2YAK1*`&%VVuNLkkDT~9QkhFcg7MUk*O`JuIEknN;Gc{!X=)D>Uq{;?=Ic'
    '9f9owZ&GXt%1>g>!SZ$k95lMY2s!VTC^g?RbvLJx3C|IQuzJw=*hCyB5`ET2yCGGDoM;-x=E4C-'
    'N`7>Ml&_;WWbRO|VL7zCurUM@CssC&k(=y_r%{xAX`u!KXvZDVqjSl{8^C;|eq@eB>c$xe1})T#`(Fw8DZ_Vv*><S`-'
    ')V771gM)0}&qVozk8IA-J6{_@uDZo)JeEaQ(z4kX%E1N43}`#h)UG7GK-bO_M(n`C<hnv7gsqWM=4=z!0moR0qa5V{_0Z0g1m<g5'
    'N@F^tMh26@|M$V-s8kqfu%1e+F$JebgrI==F(+d1-'
    'YMk=n#dJU$~m9xXS52wL{o5N~K@11|(O_@L{@yPu2I7ve%Nk+0Cz3YSxfgF!qT)5iBqANq`9DEse`NbqN^D`XtdP<O9FzMN+;c(v'
    'kD48rgVah@6a*5QExk)MK5^2|1)lk@km=>XAa^8A^B^D`hg(UZ~)blW%lif{5x;LY|9TWWIbY&_ixKbtU@?8?%jiknpRdIIYW21a'
    'eJ_oPHn|UwlI(%xAMKX+RM<{hBg6=}pQ=@*k*xG?4s{;zN-1OI%YAkrsWE{iw=BRYZb8c-'
    'vG@K0=zzwTWa_fXQ1x;waq@bv5Ugtc*v~H{?7}Y%;C5)f9WO}v!a;u})YEu*atJ|jDE!*4HJp5X!Rz6>w76zdlcO`$A&QX+m5l{Q'
    '*bDMJ{{1NPh4y4?~P;#IvBc1EKMF6qPT6RSE@&y9HLo|AohTiA(X#dSe_wea?tpD(jrFaOe9R<U-%<9>o!a8IxY&*-'
    'QXzL5D;$x}wdxUYofbe9^9DUbcHWzlOH7aL>@lh_BIW2~iU<DqU(w9uxcC;x_UU(hRe+doy#NYTo705KMOBDdG0j@toL332O(2>f'
    'meh48)*lsMo8w*+DV37lL!Jz!TRLHNf94uUq;fo5l9KaF<$3`-vwB+W*weznQs*z>)DJrpW)I`nDE#qcQg5W+TV-'
    'N)k65^6zw@gXYx0}-'
    '!jDt>C3R0}i_!>*Rx9wz;_18c)p)Ugne_=977%XdijKvrN;OS488L3s1sje0!k&sg#;|uiCMG~rO)}EBn*Uw81;Vt3xfUZvY&>xM'
    'gNu&e;z<~Lxo8FPOevJDxxG8!Vn}}7#;dqo@l4d=5p?U$nX;p#xM_^L<qBqd3TC;F6$$=_*P(Lb@2mm!!N?%_C)ebRu0#O3CzHal'
    'KmQgM6p~i8E6p&o1IUKZ9c)ZRwSZSt}cADEk4uY;f6Rn|K;$4guMZ$qq2SK^Bd8asXSf~^b_m!ku-'
    'BH!qHB{K6qoMV12SY^(EvHk<{jiUEJ3=Kjxx-;SQ4kmd1Cha_25vTHex2mOj6S>7{u?#^jtVQGMI-sdqPL6?RgPPYio$+XTEx-CF'
    '5|U-#`>R81%b2F{HTN66qycMa(<A)(V<?Tksj7EIf4~L4K*WOZR-'
    'X56#$6AtAeo>69WJ#r99WA&#UY;o0kFON60GC!_V}1_(<FxE|{Gk0=UH2lIsem=2h{kEdD5wKxn;{Q_pM=Jgi_lP6rP6q9j%E@Rl'
    'aYFLHWMQu_62z?d)JxoO#39GR0sgk_up*A9_C#cLB~@<L{hx7S_y&F1*go1xXbhM=xIuFrE+%o6VyC*FWM0I?W-'
    'k<7F+0yrI143PY!eb^%P3an6Vr`FKnUL)mNg!Qc}7BTJ}h1yr25jbEIE(J?wkwQ}3&DkD51{^;tV5|rGN(O7+YrAV40T*{4hdr1?'
    'wj(n+yf|Gn**XAne+tYXQpH<X+O8B7X;7NCusFOLS%gPe)OP9S719QN{Aze19z`C{Zik6df#uEy*!{twO22jnxGvzM7}`Ch3S$@6'
    '!A+|5cdwKx4yCwb<@Pp2TU(CMuw%-'
    '&J?(Cn(fwDViseU=0mQb0Pj*t20t@&e=GLP?fQ4+b;4UVRQ;mVU`>aM(9|7A;V9s$_;jInOFqvJOYuQvRwDnPol>HFFEk%zFx59+'
    'ly1K{@n>YOAIGkxWo|fB9C{B@SOLaIiZ!l?<&RO+3QW;rYPZzB=s$4=44E}w?LnqM1=cAB5L73dJa0+RIV9pDG`m-'
    '?K*n>(C42s^*8Mx{*cpDs?wUA$-)F$;^oGmuq@{^NNHmV8gm;r=(1>Z;ZO%<gCgzoN!-'
    'u86#khAJ^?ojxKgg`cKS8yxhc_m7OF3q?}Lo1%4B~x8gNwZY1vHMLB(y3XLOO|q_r~+G$l{0?+IODZDU~fK$c(s|R>g7Vr!Bw(Lc'
    'WEu1T~vJim>6Zs4Wo6FmlofSkr}~H>xk~EY^_0PG#3{#c$mC)bJIoW9P2Zb3vwgbr2?pZp6Q`m0x|qTE<6OtByp3`CfTD1C!sIWI'
    '$0cB!AfC8aI+WgBt^hzjY>^wxE_6VVp}!&pD)>%-@_r^AapqS9jo#}7C}$I17w%=(-'
    '>4OW!fouZ>LITGyJb8c|X>Sirfzj$t2ZU#NPmUYHs!vbQD8;R<3^@e@_a)WdSgUp6<w2>)P^)!_jndVXZ<<cdjeON_a^Gr>ic|d-'
    'rslmCAp!R9Eok$(N-gN2-)xsNGYF1<|reCa!eS=u<x+qJRuD4nUn9e=f5Q7H$bYM06A#&P)?USay3|K?Q-'
    '>gYF@_81sq5%@3fdvfdoW&2>_v)|Eq=(9D31nh|kiB(gFEEYbf4gOrhofGMBC>H4|I4<%U#hxajkx}s|lq8RTMIhg9;oJ_$`V&&$'
    '3%$cl6G@veR?|{9QpGQzztH1nl@CGW*eb6=t`C1k7w_higi?El$Lg}@XyQ&lzFVIPnmA~seN$t)4Hj)UJqGC6+O;02QxM*WZsJ?D'
    '!udy|^RA))Jaul|cKJ<pBbojW2mXBj{c5bh?q$B*y<BCcQNK&&4=ronJI&Gn0vNHp>2-LEjp-LBh#9d;wvQmo-'
    '7;ycuoB}UDcWId=0@B{&*w7DAs*QOE;Y}rKlOX#ihK=+-'
    'E^;R`sZW7YHsaj$ibBPh<Qvm85Q2N*=1ztD3io`YSR&<d8Dp2CHB>h0JvLZ55+Rw@CNyQ))eC-'
    '=8f&>sNS~(*ts)<xNEvoDRV4#ud<?fqN(0v)cQ<cd&vTKP69=Uhxn^N3cB#rMa_B)+GL%l;sERi@L7<OLW=`Hr{w>XCvx2@~m-'
    'yb2R0v0RAhzZ(X_DZi5JBN$#fTw8@h_RiE4P<u>ki^lTD?>MVP@i?EXN!*hqe$gw=oYh<#BwqB+boN0_?3^npsLUBuzrQ8J8E$*q'
    '_+<BmL)>z{=E1)t~iL1Lp=VQaH^O+pfSlR6#5r_-'
    'n*Yzc%Z(73qX?4<iavEgCpKWzLK;lJgTkGDA%AViI_y|H&}bOYX^{4aCYC=pf@#^hBb$%9<a<AePguVo)(srzn!NLm0|4MaH~^X?'
    '3xx4S1NTxtI*?aiQ}UM@zAFXF4#L<m42#sygx6t=q4Z65fQ0fA%sV%}NYnHJ&p>nQ6VeROR8`sY66reajTtR%%921m6exWpQN?^U'
    '**GKslXCi?(6<fKbu7XoDmEN^UK1^9~o+N*kR}FiV7=*|8_ff|>W7N(!TogDg$Q%|P%mma3m&*UxI&q7ITAd@;&|#fyYYSR}HPbs'
    'DVJwiZ<}f8qzCuKsN+^Hb%mPj23xA)IJR^|X@fJ;7)6SZB3iuFRYzqMUX;n$YL{bv93hHdXgqNlf*8+KByLoFDsLN<=iIvu+mD7u'
    'C6(gOG0rlnX^g8Pt~IjHOcR4r(VVx8|KvM~lQe)=}ObM&aVLjJ(hSTv6#HXiTZi%>bE`o~IC07Wp8rRJXZ9I<XVefRz&>4|quN=}'
    'zk*IVi))RyWxUECOyk;lhcJ-=h-Gkuj08m}H0oEiEE=)4qK5&&ko7%BH~?n^9yg-'
    'C%XvK#RguALhIYoBB;x91~X{$Vkmg^=JCSnjyEgNrl$&pE~0{DND`A$*E_2Y02^LA|jhqO?SR0C>Dq|#*8jmV6>738X-7HCQU25-'
    'O!m(pb9frpeNQ*z+TsCX=l09QqF#5@}GO1F5WYf5iv|g(kwIK5nH&o`I0F1#sN&|JE&e7?Wk={ombC?DXT<wRjBn@q>Ht7Tz}Zzh'
    '4amXL=Db~bb&TZVg3-'
    ';n3z`xqI)jr_x9j%tF^E7c^>`D_6FT~Yux~L+GhW}Xku%wd57>v)5k<bsWrCd`tb!Mjiy0QUFsU?!rDp2>@dcr-dkc{D9B>nF~yr'
    'mCRmD<S$lS1g;1hiJ5M@~_cn2{#WnMO+=SJ~YS^`&DZQOgm{uHNVCW3J{ALJiheHygx&=8(n3RQQHW9JDQzQ(ptY%9EE-Fb92r;?'
    'b_-I@S6fvoU(j|6h>RMF=Vbpe!Oma`V-Mk|YlYCBGhgoOe7GyKSGCdq^-^W5mr!9FUYs-'
    '~{V}fIR0$dqu_jnsI^nh@5GL4Yl$Wk>>iH*&eSf_(sCrpiC+;m6N^KI$(hpEUhYl_M+#I>Rv#U9a-'
    'u)siJZ5A1G?9CRPPMXyc#24~1d|P6jDtFc?bPpS@CJie*G36dfqBln>l-0X4ub}ZIM)yKe!pz^!-'
    'mJ)QD5X<;Ii7qMIXq9l%d)G0j5tP6ueYy)!X+FVN5+vmWJybZy;S$5waf-xH6qNHUrx3EhBm?+R5fjAy$wi@U0MOdUFZinqB4M7t'
    'Hv(2;VH__BH$OYE{FM|qB_hF`;R~Z!^}}F<vm0pl~)%Zt=XK@4k?-v36#JD;(v0Y?p;-'
    'k2*ImX@|f1DTxE!)+Kfo=&y!d1^Nc*hY7%6ua3>L*o8Cz*B#4}SSfpm-'
    '0@j`dP6ORX3jL4t7R_%Z6Hmca`8%CxDoGzd*q!J{>P6w?aCIrtwD~UUm3?_!TU6GSV8fL)>P9LtsATmb1`!-'
    'y5bh*#k@U`>o`SWwcbMxtp)Rw)Rkb?2u>DVh2b{UO6WrVmH3-'
    '>zKnFQdV(Kp5vQysKP}!_dS6Y<MW%|qeo!#1fgj0=B3p@wL{3MK3iBv~0q35?F7%pS6TC(l%7s?a69CMwpTCJeWSCsAMB%>bb&Fy'
    'rIdJj~GQs#rAsX0A^_NksOIh%~kBtj3j2q@evgjH_WF)W#~`<7$HemS7!<4Tk+Mtc2LR7qD7A@bZb*UQHf9IcrmLyUSm#;Z-'
    'wORWTG>*&5t>V*<}!epiDd?rI~dD&0`!OI5&rnFg|7|a$ui&>AW5rt9Oz?^v+5y&KXa)|i4w(I#N06-'
    'ESvD67hG=R6U&(|UqlzLL#*c`^Eg#hYYS3&Smlm^b-MaZ3D`>s(L(wx|e<%@+bMT5ee_LnMfCwxLGLUD;KCn-'
    'pX5M95uJ>fQbptO}r%z2V3JUS#uN-ELGGm;Q7^`%KZInaR|-%27q3?;5=jq37sF^0Y)$H{U$x+D&sVobvu=BFa-OY*lu5<fLwa<d'
    'lp5|TNL_B5;rBmWkOWYAM^*kMZ7NJb{r<?{(mvFtA{?#t$IcpNFuKxPJsWVz8~EreQsjZ_>wel4Lin37;*;-'
    'SuasO^2d3zXA03z~@cfnNrCeU6aVtGHoQ590dlOYRBPz!E*PBIsbVo+0_u_0u{u71UnaMA?&i(q$0XGDvk$HtCZG5Uc7d*=03fkR'
    'By#9hmeqI+-6xJrv~u3WzGqBT&K3u?g33Cc;dm)DW_u84&A7za2g8gIJnkro5EcY^Wm9cy!VKU|U6GD?9jwYGn$cn4{-'
    '|%4PSnL!&wPob(T&tyn6)G*LkUdvM8QSq(!Vtc~=3VL*r=L&oc}unNV2=}=YSg_#Fl88`p|61VJgV6(?jtc-'
    'v%xCNi?cMTmuI7Ktv5b}o$bAaxk7AammbweRbcH@xgm_Q0uS&CK*D<Ihy?jJOZx=#f7BA%&|;Sq~@e7K?DGk#F=y0Gj=h`$kJQ=X'
    'lnFq>2I%&zfmf}z_%386}9d%%`On?|nv>ae^AgaJrE%8SL(ENuPP1!Zs1CUqFIwClph*2Iqw57cwa)ai~?Ksz@pUKD?fG;QPdNec'
    '*+e$x!oA}-fd$G#LTv@qyl*lx2_qit3$Lf8Oj1t8UqyQ4EH$M(p;6TP1KjEKUDt5-QzmR<t?ND(yCo3vXs$pz`CH%Q3-'
    'ViKada=>_lOP}<Zb9WfW7ajF0YoCRr>5V{^5rt~qP>;0@2ezf@EU%`TD3R9k-ayX@-3LNkY5_!b(JQ?{Jtd_ZWN4vcd0-'
    'h~)8T?xo=On*EW#(MEv3EOJwpI}*#crc=7zvDY<U68blUH#@(qp7!1LnJwIeEE-w_b6bxJ-'
    'BOqO;}%5BlqQ{2Kf4M9vukRmC>d(^-wHwl)UDiX-#p!5z(#g0`h<y}(<$dPBK?~YoAKy}NW-VXKHCjFXtIXRp(#Rpl-'
    'Y=jA&$R)xWqRWm&&f!S_hH=>1Vn0HvA^F|{8WME}Z835gy5~7&=Uj9^Z0LqC8`x5uDOhu2rQ1H;Ygs2U9dF5DWi;4}ih6~sbtL7@'
    'L?~&%y8F@^P#-z9P6zvXIB2$wQ|^cYEP#tR%>_c^`|8=v=`-'
    'QN38wv{%ch6>#^g0szO#Aw7KMwe{qMXgHzKH~R59d_>_$9{W)G}KzexN^Q`~9z!S-'
    'Oi)R(7T<uVCg7{gB?Yf%mkrbt=eafPA)ua@V~k@rN!t<Vk^VtbP`?;8)hr*i2mnP}FHDp!0O8Q8aZDNJp?{XhC9+eQ'
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

