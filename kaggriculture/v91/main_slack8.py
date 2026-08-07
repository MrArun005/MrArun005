"""v9.1 slack-shift: v22 route, WHEAT+FERT sells up to 8 turns early.

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
    'c-rk<O>bOBlKd-%&T~+IkdpRBOFd&@Xvv_YZOj^kVPIylz+(2`-P>aS`%0$Be%&uJBO)tbQ?h-'
    'dM0UTb%&K~ok&%%<{_m52|M{1H{^OS?|MJa`Pky+1_wLE<pT2qWA3y)s-'
    '~ap5e|`GLKY#w^KmYMRpZ@jZlkZ;N>^}X4{?oS~{`S+=o7dl8T|fEwUGKiz?SA<9!y5eV<=g$yZ{F>8uRi_%{=41P`;R|7oBihd-'
    'SyiyAAeY_Z*TwaPv0ER<@L+Ie)!?|dk^#a@yUMo?)}{e-'
    '@Ltf|J~h>_Xe1L{CLQBA3HV6r$PO2^Y+z;m+z+|2E+RH!|Ur;KYe`8`ww>(nvQ8Q5;Ca66DEIrJgT`xuCHG1?hRr-'
    'dH#FyuzT}PA2OSJ@UZyr$U{@(9vuGB5N{@aIyLgWneH6lWZ;Kq-mTfYwRH7<cXRsqKYv==$HV;mk%Gl1Pnb;q;aM-'
    'Q?(O^e51Z{fnd{-'
    '9hrdI6NtzaNAT%aeNvEIXK0SGqVPCYAG)q5xamB)iB{Xhfwp<TO$Xu@TCm4pEtf5wOMhC*&7K&l#uT#UY)BiLr3m)5SPdKyGVBoj'
    'Y&097nv{!0Gao^`N1V1&~5d9R|wSO|F*6g3m$xn~{fct|izWWB3yiIoZJp57No5A(*{%G&`uKBtDWsIxr3GiJH_sie%BzISRj_e%'
    'Q%eU9pyO-~O`t$DQ{p;)3|91Kcu7C5pw;%f4y4)~d-'
    'Mszbe7p7C?)uj_dNPk`IKA*%l8(Vu(>H%9+xnAj@6CRg<ACpyFL9Tt@Rh<gI{lV)|G?JD%2`*JzJpW2#fN;Xy=f@O1Yrf~Y4bIE^'
    'oU7R*6^_TJK^|Y(EszRvAC;Ns>M;<IvEy>bI{Fvd?d&llN&Vh#xf=u_mpLz^@yvakhFauIS??uX4*^w!`VM<aw8sV3mYYgnY%|az'
    'mWx&IQ(??k<Ngkd+uMtEZMz9#7KJQoImobpK=w(dF&_t@wM=4XV>(te@)+7*K~Se--emxm3VPe6T|o4Dg)T$b_O3e8;yKrbnnZx#'
    '|u$r#mFa_)RD&{tIx3dE~ATp01g((h4}Q>-Gf4YLN<Y{fR4yYbY4EDs+nXkCx2^`JIgXd$~~u~t-'
    '42)`>pemv5|)~c=st@N#yYXFmACSeL2R_*a*KnE5H}T@6Qa~S>MNe_SgRa=@@&QhnflZBoIk&ENxNB1!1|K&Uw=uyBxpJ7mHpPZF'
    'K4I<-ml~7@WCHa|-3~1Yw{eA;RadFPi*>Xed#hNS=gHR0o;YLvi3R@Kwox9De=X)y=;;)8B}I_I)fv=Wnv-9>yCz4ucJ|#Xd-RMs'
    'u1BP36ZT%N>19gkeM^W%59L`2$~fu%{9K3a=KN{2+#%ttB!`81Fp%=h2VwA&TqrL<S}_2RTxa)S1)8A0B<Qe9-'
    'iQ9dElTr#6QPVQ;%5Gav6WWa){6HRB3#379QhNB7LEhhJ9~(qU5Y8MB#+td+vN*|v%NtWCZO^FO=}FOKfCN7LP;<zgXlk5KsePAl'
    'K`3RmHBsm0xw6^4qOS{S$#N+x(jVdO<Zw)nvqpe+m)Wn8797Q9n8a#ndJ%^(3EhY#g~C1Mb8{1q{Voc#Vics>B;q7Q%xzT|R<(dU'
    '9In+3?04v%zUf@OlZ6k?8o#nGGdJb+6t%0i}zOlm_baqVWa{Zh2dCF`|B{G+6)0zVS(f@P;^c~cGg2>|H%b5kHfsC&@HyHr-'
    'I8wzHj?%0rZLST`_K)4H)dmNfkC0Mr6BlOKGreek0O_oCb$X&nhnM(c;)nsV+yxL&MV)Ogfg@#JJeS3YU854pMm-'
    'b!r`s&TA5xtw@l@y8GM0YfNb1^Q@FJ?K*ckgem_TTPqZvOW1U(ZL1RERW8nztNGG!9&b=QPF1Yb6yB(#Bj|73eKDr|Q*)uqpd<@>'
    'ulShmjsKekXr6<k4+|M`JaY3}e+^(OcWKhbPan+(GVcvR&zTE;{z@OkYUJ@|onr3-'
    'MA3Ee8{l2g{j}gE%~hPa+?kj4R($vsrZy+lVk@1+CMAU0Ir=14rxj;P}H&Gd6>e)ii0JqpJZHmExm4$T@{o6Ry9J1@W6@#K~J5Ae'
    '-E0BP+rId+xos9m!56ZpA-'
    'N;tlV5b0PAK(>uYj%_d{94w{n5@Y+@kISbM1!^|nk^E7q~BlTj8mrEj4lSwLDphJksm}Op+YCf27uAOjpxQ?!nJ-HlUsB)>*qfl?'
    '_MyJQcdBI)45jP#q1g)NGZ<dK1CsebEW>ff4JQ$we8nlA=p@)gVOK`_XU$`+1e&}H)>@Uk~SbH%5mDbt2Xg9wg!LfFZI$sGe9zzQ'
    'O4X%7wLgQrmHEApz=#It?fJED+mk7H73uHsZ6;?j-Y2{Kuqj&-'
    '`B{OJV=>flTdPCdM=pZ64b{ZY#MZlSYX^bJYGE`O_DX;|Zn}FU87s~W<m~v5N;&%N4owIYJ&4>@}M2jZO<PW3);Tk5y0ao2m=Gd#'
    'WVeKe~O91`4C5uXRf^nrleLPNT4DHr{DlTiF*GCxy-{}zKO86x*i=>K1j#!)Wx0OMVkx69Ex$G!?LbAN0q1-'
    '(s3QfO%ef`&8gHrY7(LcbP%m}0+XS9jUZHH|+aFFNV^LfOEb`#{Iy<MXIEl1G7vpDO%s-'
    'g;O3sqQkpbB?CjgU8?jL<liF#q1d`~9?mL>R>S(7{+O?rAlskih95Se{Qpd9a6MvJPd0`LfA34tW+{D6M#uO`%+KfxMi1K1<l8!C'
    'tu%1z{zM^<c@bg<#aNY&H%W$mgq|e$j+033*&elj|Ia;#E&igqsV(OK_2dzqE>R-'
    'C%~OT6g@Wdo<qNJAa=yrE78!TW4P_+`mLxioz0AZl{F-'
    '2XO$dt;xFKbo#opC|CCMQcI#iQLKGTdHi&aA<dY;+vOFo+RZqwlGc9!{b935(XvYEaehoc-'
    'h4t0#5ckJUzkyOly_OHN?IgpN1X1E0s!-'
    'W&Fu7zn+<~(k;6zCRiI<c+uO3(7NG(xRs^se(2zn13i>}<pJ9#oVnBE5U|O^=&dT2==L-'
    'gR(9!@}PnAsKYJ_PV<fLK9i&jXlp7Et$f{87Um>3DDFvOa^6iKXXr0i@iuk4bBDqR=|00}<iuIQ~@5XwMb0xS-'
    '*(Vap@d|1J=0+V+~dCkU_B6<DbEE^r5BiMz1M65AHQRy8cJ=!NjfVUcgR*J$QN7%rN+X1yOJaS5zIQ?ljG~;|J3>8jJt6<P1P5f&'
    'o<N0MhjLZ$yKn~0kSu|};Yr7w=LC4WE#X8-'
    '%$BXxK!gwRv7LA4Hw%z|f%#LKc@su9^*R2Iq)D`+MI2l~^YYtkPZEA(|_g3FL9jH9e3+M0Y1ksV<wBe0w6L_h4^cVP@JXVi!M4eb'
    '~R5XAIHsZ2|W0T{2kQR1JMC;K4j>{38AuKXaGYjO>L+nJbjb`-'
    '1E`(*}?F0*uCyxzQp1mCB=5z=G&M<$IAh<ebVOsg>7Rn?bYeuR-rYuZofUJgj$mh=nkX@s&8jG0U+w1P_q??o8QQb&NwoSeta)}P'
    'BY=woAIb&yHP*B?a`M2G+$u|``DFqKJ1wrU$%1+h>Xm&HQp&-'
    'JYd(v1P=;K!LS1uV(`bY{Ufe{A8(50#(t2Tm}xh`)YP9C!J9paX^Jy_L^@Jh;1xDptI8}~5!h$`q^V1uz!HYhDYg<29J(KX(f-'
    'X38t%GFQsT(S6iRNp_afcP#Jid;el6qs9)IK?Vg^g1`k9`gx=F^jV^WXhGtA<fNgVf9&ggjz=`tYS@qlQQon^A)lOa_P_!#-'
    '}eDniCW}Im$C6RMi;mtM8Sl7<b@hQXnZ#>^#A8iwBfa@U$^khb1c`@047Ch8;bLO^3=2Sv#2G;+6~Z7Gw^>+*4t_E;X0jF+D$-'
    'dP{n8VAI#w;h`)M=V`j7ii!;eaOz_u3xFts1Dd<5tqO0ddNnE(xgd*96{(pF70ar4wVf6yG$6GLIS3i|=o~CXvJ?;xu*ywbkC0Z2'
    '&~+lLRPVx&J6yPC6TPL;ULv`l(bD8hvj&)GH6}7-'
    'UtASOG=b~ektR8M5pCXnv9Wgv(IaaRO5Mr<3(+A%ffZ`PTDKKZ2TG~uz9dt%?u>ZU-aSNX%I?XFF2EDE0SSXJJR5FP)o3|Pol}1x'
    '%1Ab71mM8qayuT=s}pdYIot__?iEdPVYIzSz!p_^r^G0#F}ZZenc^W!tRkjSq;evCgPk%0iIyCx@q8{)AZy($i^03tQhHGtpJJH2'
    'DTm1`xmjYH0#7LnE^)Lv^jKL@MYpC731LwtyJ<A4uV6&Qx(@8kSB&f_@E&1)vfsO^p90wtw5;NE#E_SCA(`}2shbAUEf~on|IdVK'
    ')221a##N#7*sTfkF|ht8J5T6GZeK)Lcs-'
    '^e@+f$5!ej$94rz)pAh(%Ss7ad3<pYN?j_8I?jau>7PSyK@j!VyGErJ`>fg$w1Zmlg=ETwnCO4?&J_M()f-'
    'B1WQG&YNX6E_*oBD!;%5HfT04hjT4ZM3JOk6N$ka|Mxu;5p}V9IeY*q{xk3RFT;_dD|DL9CIXXtLHX1=aGS3%jz@5jGL!NJBzr^k'
    '#uD-?rH3I4h0w{(r_99o})-g%HtLKz7JF`G2;|nCyyz2oh05f<hjcM&*6)r<-'
    '5&LbwHkLoAC#lMLqJMv)pRXZy`x0zaPxZvf?iiLs;wK!aZ<dgmRjZ9~Y-s*@{pcrg7YId26>fVPX!JUoHn!4icHHaW?l0-'
    '!OSf(xoyy8_-'
    'HX&u`ND75FuB4T|P^K?DT8&T<m_=PUDiu<5BA<&cm1qs4G5HyLDxm!UC197nDPv(s%_;PhZZKSuh>b8zR##u<sZDg!r|LRSV4XF{'
    'Cj4{k=QDcN`afj8v^sbnPc)8nKNos=2LlJu?<HUx5WauMb;r6rxKF9S-?oWaa5WXy#-4<K*LboOaPoHr>-'
    'CJV2Na$LJy_OxVfQq8$Ut~C}n6iyT-Qz)67H>6-'
    '0M#@Pc`MoUPJf0aMyUED$W^A@&?jF_KgjJm?trv^y<wqsllBBAT)q~2jq}k*s>y*#LtN3P)j5-'
    'aUTBegb%t#e_OCsnXL?#uhj7?k*?xKKxEVu9V1tDukot5!+<iF(kEm%XWuNxP1fk#H?<fvRTUlve4Hm`ghVLCVR`9~E}M+w`H(9-'
    '4P5L&Glub1AACEbO_DEddYP5ocCBPm~xM!+hSm)G_jOYa}|7=M`L(RJk_HpbE4ZQAE1(*zKFh3=xd@aB<>fi;hno1o4m<0AN1<}R'
    'D5Z2RH^0Yfw=m5A<CLgy<adIRL6d-&@)B=GQy-r8+wLL!HtbAC;w!&PT-'
    '6zzSX)pabDjE~?B7#5zai=)r_OXI?>@I^(7FlNftIHx6#62ibkQ~D#5)-`(tnHAg-X_%0*PyCI4Q$bJT>Qe#x8sPdfKr{!K3q7jb'
    '>W2`0gw4w0-B_a1Zes*WFVqGKg+Y0JNkKp?p>QBU22Cogb^v&c2DSm58xZ)8mcsm_mDaSX`xFscIBKGW=oWXgHbd~-'
    'lTna@1qp#kuv?}(>f6m}B*q~wEH5cmg?x>L-'
    '`jT5$@*&`ozNcx;D2FKNf?4_yo|+|0^qhl7#gWnlc}y2C6ka_A|n*^(nb<CY}WRa@!ro%65);J^Z>BV3DIATtgEB|3p5iz(w2~Mz'
    'X&&p4?`BQ*f<=I(qqyrGcS}l!2h&LO8uKIsh82)?N+T>xPass6}^ui)lvjl8mq9cuYqch8a#n0gIiy>`GLyF82IkuxI~IO#40Nuu'
    '(K0Wnv>FB76$Im276BES~Jm-'
    '$;IHSF`!k?Ksm5^r#kYouN*J6l)cqSRh>zLT!8g92E#&$DyQGd{c<_#83}dIE<2(9VA>cu4Bi6pbTBCeBs*nv+O77_SeBcEmWSjM'
    'i{dgufH-beiUs$?OjDIGaWsTWy!LBUiZ;T;rbVS-'
    ')6i&kVP?dp$c)eu^otNdIy4eAlEhjjQ?Qb!p~C))dSQPB*<rY;V5=c+$unCt0A!r<RG2>7vMX(B28<&i-9!&V)7#`yM2-'
    'Tp#0lKEDp(i41Fb8ZxmOjjvcP0OLcyt3Hb@>;WF4pY+-'
    '?PK#XH=$B%wua{z+QDJ`ETL=7%<|b&G>@QjE~jLSlPsqo%U{DPFQDX%~`yymPM5tB&9C88FQY5$e+8`aDN<F7ZKf;tg2(AFI*#3B'
    'Oe&Dl|>Qq@!79*^Mgh!Ahlw-SfDy(!2qVqUsKX=2tFtAe;!6lp?jHxD~YR0vw-zR<zK|)Pg1KwbeClajj0_kO-'
    '5tc4R7x%d3as0=H{XQbs7mEi6q}wTZMO%^OS{e)5-AfIV%OZY?35xW_*YFF6aayYK<KZ4)-'
    'P{_T*Pmh1ReAUB;0nX_9)M)^l3@KP!@cEOqf^!PMG=pb<Hx-dSqAxTxlVLSff5+N(UMl_?Rmo2SLPYOt2NnXU7>c-'
    ';+#9s^fVZpUb?WP*4u40z|^AYG+ZnGNEcm%vMfiCOK4+*-'
    '$baZV_WK$8)R)&ul5|NT0A_%4Et>G4$P*_)&_hIvfe>sj^hR$;2YYE3wrSK_klxa<M<Th_iY1P(Q1v*llSzTintxqa~LZA-'
    '*dBZ~|7{})|s80~4cPyAgI#QVP0u;Zel?W4J)=7HV|L440^>yx5?Lja>VbdlRT%2Pz-s+RnTUuLMLVQ<nb!5p@O-'
    'g_t?)K`IM3nX9IGrUF(IJ7>Iq*Eh4NIg4UDoh`dX~0CEs^P>7Mi75josfaNu}qCcbdXff#JuB5I_Gpqp3U4a6X54wV4>~r3$^Yun'
    'kw2G2?Mb<)+K?%ZIPe2zH8huar7Q>m@HOHXb8Dg0I#A<5k&)9>)4idr#(~L<XaiS8{H;sG&OOfi_Am(~abs3YhtMriV5PA^?WGd<'
    'f1-'
    '(kP>iw4G_n>lXFy5_(Fak3kibSopG+5J^gc(HfPy+HjTn>cqD0;*7~Y97qnrjFa!N>OExLbPGeE_d`n8+o_t_3<fMI+gn|q(!>a%'
    'zUY{<Uak$`q&m$_SI5T;RxW@Ze@+U$W!W!>b?%5&>*Df?!_jndIjus;cCIGIDs)Lir)wwBy?Z*&N@2fQpDTFt<ipZcA(hH6)c+|3'
    'hiKU(6IWVkl*J7+Dnu?1$iU$M_}TF{FKcTdSExSR<(|f<txDEcR5~+t6k+M^buATyc$c=L{OV&qlo<U1+*MYd<M_HxpwwD>NE4bF'
    'uu)bbj*3JEsDMxUpI|UG5*{!WRydnKm;0fV?BF^-'
    'rc_sSEkY^d(;^3G9qiQBGR%FJ^JbAGL0x9w0gEl4hNy2_OUI*<@ubTA3m4v73a%{^q6TZC*HS90QcS!+TS!*_u9Gvh|LpGxiQpuv'
    'ZA1I@L~4GEc8P?t>V~o!TXRdbiG(XhVKC`K-'
    '=}Iyrd|Mx573fw+`z8k^)_{cwRv1Wi4jNY3IS;L<gG4LSrtO^44fqp%XWr3UGyhzyS`d!sYL}0ssgZ_0<TPWX`CfC(%z%t&_AMV9'
    'CKgc<0tB(Ap0lAm-MzTa+@@%je$~N;v5BvLdBRu9Fsc`B6wkQr!s$qJ>MvrNC{vgV@EZo-iw13DG?@`G5COV2j4z=VnC_0mdlp($'
    '-2s%$WbUJh7C_unL!!#!mW|g5cT`r_1iad0#tlp8$yg+<uDewRK*uLoFHl+N>^`G2OL}u(4S6bPX06bwKSj23VL~6@~ET)!Vw#Yj'
    'X5lsBtj{KQMgPpVz*FCOQ!b9jUw9me7H1M??Qi=nRwsIaYQotB)V*&W^Q9<W=LT8VjFJOX`7p`1P5HXWU`b{NLrJ2vn?-'
    '1v?gT$QS1Pc{_;y;WMXD2`rqe0Rmi!4i}X!%9rqGC<%(l55U8;?{fe#IR$LU$Jq$8Py=dU&lx8zZJI;duWQLd##-'
    '#8_%adVVnB0a%8;F%-(1FIKxQs-1m9<BRfh?zU#h{?1&SxY^iZHro%8YrJ)9PY<CSu~u)LeRocEQlej-xzd-'
    'I)#)COJ8Uv#L&fKBW2JNKOh;0PM$vcq_4x)p*d*Yo>+tQiX@RfrrSp`bjFXt<)5vh|3SO)Z!u|<{N_)m2x_j2EV|}0-'
    '>{WH3vr<mTWDsc{?Q$;!PqH;S#xMb{onPWahq8iDL9Ek!A3>83?|{a{Dus`*}^X)Ip+y4@OC{c#)6^i)@&(%7fM9)}kur7lA-'
    '5*59@=KUF^Z<hJh_LW-tTPe8fe6MRN*dsai{%FJ2HDn`YtdZYKx**uM#1I><-nEv^+5huPlKO%e%)l!x#Zj&z6388~Pa0iqNl}Q-'
    '_m*R}2GV2b0C@Qt)%~VGV#5>ke-Z@60>9mZz&<tGB3?(2<sRPac`;*?M5P}x@Ag@xlsX00m6myA{8zK*QNCB${6A-'
    'E=Tf}6~Tg2RWUWJPt--;5`kuj9B&_f<S)NWAL3f!BoUjHSzVN-'
    '22IAb$d%rzUV_8VwXn3BhweqmF>>55}I3<LnFd8z*DepoYPYnx<f9p<Ss@ssM)e4L!2#+Q~H=8m^GW?H-'
    'R{jbb6Is`MWq*QC5s%Z+KADKC=*mgr=LXE27?$P^*&tGz*Sh87edP9InLpqW$Kp(Ba4P;%GN$rRS+}mzR6fot0BlI0qFpZAJwr0?'
    ')7sC`)BE2e<?JUy$TDx~Y9Nof2WkQ+;7e2Z`M|@_fb!p7YX9#9{A?OwMU}`J5?J*;oo<~9ROl`gMF1rEDw9S5b(ZtzY^S<KeQpjA'
    'pKp#X5M(W?sFCi%^h32Ra>B-v3yzH3urru*>UntjN{WHZq)JwAr@I)qkskaMfYN^%U6SiVz-h-'
    'R4_*gZ&)>mb$Tgp>cO4Dw7?h*C!-4K=$>s&-fCX=%6%(fxcXNm;jRSUtCK>R}FEq6c~*8)X6D4}qPZ9iRUsvwQpE|W=isN1SL@-'
    'WH9#8sGeN^L<nGc3}>vG;vsWVGBeR&rH@kpyglvwTWh8CLh07%@13AagQ}kg&+IGEiHM&6rrHgD)pcjlkLTl+#md>E~%{-'
    '>0_)#&JxJqCyODNhwFROM(Ur&9=ZrVI>zCbL>A`bUJCeOOR>E%lK{4b*kK1r_end&zdx>@XnR{E{Wb8sb*HUZC+U8ON{P?goc^eo'
    '&9Gev7uB{@#T2(S>*6MFE7ik0y5$lLA~A*3rd`DtQ{Fg?z$x{{q<74o7OTLbk&GXUw%0n02|sNvqR}rZ3GVJja^y+!>#NG*`P8=T'
    'r0;u2MZJexClclvOq=6m?2IdfeMECpju*lh!`rbBtBZRVW-`jp($TL`APs6Aot|nRmJEMycQ*oYpr@zw=Ia=peL`&=jnL{)g-'
    '_e4PRaI1l$gE6R|sf<mbcsG&>Qno-J@1XbUMsKhl6S-'
    '$e`rud37vZItOrjeSA%BlXH}a)Y`QXUY#<ueQr$+M?R61VXN?TQ?kuAtkGcF$mM}f^a8^E1`D=@f57Zy~A7I3B{M4EnC?6C&l~Dy'
    'jX5RZ6V~e{n&f(1-VgT_AWlRQ+C==F|1H6TGY#Bg3J4z))2j^`#Byj<AM?nt3<OSsLqSq5fqm3S}jd>_zmTWU5+)b7gnYffccuT-'
    '7IC)IlZ|_j#0{iN=(WmS2Q)J6VN_Y)Fl^>k(osJ-xfiAo3r+h-'
    '>zf0G3Dzm%9P!F$q?n^%9Jifc|EH#>Gs^pq$`Ofd2W*H<>QHt)=ZJ%OUnz4%EZ^v$t}!#C1v)6^h$;MOrG8HilPLtm#-'
    'E~gtKj8x|AqwYtH<JNM#acS*Ny=B7G^YmxMzsWq}b{UzI9H9iyH)4yn^Z?{qq=pvWjn`sO|%{LQfS)~I}F&RxZ_!$OClLFG*QLlv'
    'kJzP=PCw?sFS6c$8itlz($P!&Bu*~$v$v_}=%98wG=CFSG=MtGI_(j<Q=HcDSTk0rHMLnp4t_d<!QT2s1w9np^Qw=VjQoG)wc=z='
    '(S+A-Ho0<hO5NDa7362BFa{i#)xlb~==ku+m;U}B*d`MXFAgI=+n3LxS8gHcI!O?^UAEc=T~`?5J4-'
    'gU|gmYG4KSORnlaY+T`0F6={yxT3AG?>n?`@=gO`cTvRdJie5>lQQ-'
    '?+m{TK>GsWv(MtzQa!lr^Dnti)cHB0qk5o&t$G$9ga&j;8&QqqO&7vf%MjE-3#CsHKrEzhQV`AWjI}mPdis1ZO;NJR3_Z-'
    '284%7WC2f%9#XwI#nC)mfAB4sf(d5OyW&@LfP9(vBhB!`k914}i6k2aVLDf?kyPq8z&B4E<HwSHVQt?|9Tt0Q7K7wU%p<-'
    'E+LSU7RbX;L*g&-!ztD&$&#DSe4isDKcTbM`SHF^VBA92+_M=%Lt7Np0kCHc`*K(dE2wS{G|-'
    '}$XP(Bwk2PX)m6WR&`M&%L_)TeNuf3=l;!*;Xaf$srSoN<f8}q6NpwO!kExi)L2$lK@`CGgXpDV#$vWHWcpF{L<!iVA+q*gCoGEJ'
    'Uc^~HYf9$9p~G`N4J9lM3u7kfM<&il3YjD;ero{0+8^P7mA}<*jlm+O6a0P>M&;M)P=9Ii60+cvgeqo(;2CNb#7L?ApRJG+QzMu1'
    '_8m}9pAKw*fmwQFGU9}4EkJ<q*^k`a)#$^WTZCN9UZk+=qE0ci3ZPnMnpBm)uem`fRWTjGpR|t{gPacjv9f4gfS))s_O=fH?8!^k'
    'U8Clady!azOwdN_?d15z45)M-'
    'a5v8L$;*}EU$!`=##SOx}v%{cZCqK@ydRqZdXGNwj(|3DH+|MO$&w01IrDY6PL~Mw1#lD5jIgR`LUNfaR|^eTU4yS+z`NqEib^KP'
    'U~G&)uGWDcwQVVceDoV9RV?1r&!d$X=#V0+!js!#4T*o5W|G@D3VyYM-'
    '3c~ZLs82fj}l2rFUbpx?1U3g_@2)jyyX(eAEhuilD92Uz_xP;)UpN(i9(L?XnRjbRv}qdzxH!EOHJ{0x*oj))w~>5)H}c2BVR>Gq'
    'xC|3|;X8=R7Yu;54-'
    'O%|^8pQ<4i6(i4>RD&r$6g2h5uYDySMd9Ql3nI~QxAF8j1T2F($9O8|(i&Iu~!T7jf(_9QRX0Osf&^z1dGU37orca{BrkC?VMUaz'
    '_rowl+NcT_+8ya0?9EF07h{m2$zmUJK8!<DQIT(BGW8P4j-cCag<_*1qn5SLk0tsFc!*3-'
    'j_Xws(StD|Vo&cYg=g*P%M4hhC4x+AHp7V`|-BYu4mMk>urIG7IjSTF!`6x^qyZwKOn&aX'
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

