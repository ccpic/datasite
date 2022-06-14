/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

(function (root, factory) {
    if (typeof define === "function" && define.amd) {
        // AMD. Register as an anonymous module.
        define(["exports", "echarts"], factory);
    } else if (
        typeof exports === "object" &&
        typeof exports.nodeName !== "string"
    ) {
        // CommonJS
        factory(exports, require("echarts"));
    } else {
        // Browser globals
        factory({}, root.echarts);
    }
})(this, function (exports, echarts) {
    var log = function (msg) {
        if (typeof console !== "undefined") {
            console && console.error && console.error(msg);
        }
    };
    if (!echarts) {
        log("ECharts is not Loaded");
        return;
    }
    if (!echarts.registerMap) {
        log("ECharts Map is not loaded");
        return;
    }
    echarts.registerMap("海南", {
        type: "FeatureCollection",
        features: [
            {
                id: "460100",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@¢NDxBrCpI^OTGjGfBBBFFB\\PlRRPJhJ\\DC|K|Q¤kfGL@PDFAHGFMFENEJGNODK@OCE@AFAHEXGJEL@BEFAD@BC@MFGD@DAL_CKAEN@D@BBNKF@BEFEDGFCFICMAEJGDUBGAEKIAEHQJAXFN@DCBEJIJCBGACWMCG@CFGDYFKCEMEGEE@SAKFELBFEDEIEBIAKOGCEGAAACECCBCABIB@FDB@ACXA@CCAKAACBGAAEAEEAIEICOCCCAGEGSBEHKBIDA^IDE@ICEGBOCKBIGE@CAGBGGACJCJ@HDDABMGGFU@MAEFGPMFBHCHBTADCBCDAVBD@@AEEGAGEKABGC@CCDECIDIAEGIEMGECIIGAC@[AKFMDCEI@CFBDAAGBGCQGACIE@@AOEEDKACC@EGBCAEBGACFC@EA[CCAG@ECG@EDC@EBCDELEDC@OABDAFDDDJBBBFBF@HDJMCWBECAEA@UVGDC@ABC^ABM@IHGDABOEEK@ACAODGDK@EGDCAGACCAGBKFI@KHIBGDGNAJDLFJ@@EDC@CCAB@DCAKBEEABGAEBADCAAFA@AH@BABBFADBBC@BDADGA@BCB@FCDANEHGDAD@HADBNBXBFHJ@FAHXLFJBFAFCB@HEFCNIBBD@HDDADIAASCEeDCBIECBIFEBEACCEAOCEICCGOEEICABWJC@CAI@GAG@A@EGEDE@ECG@ACBKqGUIE@KJAHHFBTFNBBABCDAJQ@IBAT@BFDBJFF@LNFFNFADBABCBELDVCDYL@JGJIhABHR@H@FCFARWRGBIAMB@FHHPAHBET@BABCCMCAA]LEAKIMGC@C@CDAJ@BF@HDRA@FCF@DBVGHKDAFFJFDNF@DEHI@MLEJ@JDHB@DABCH@BDFBBBAFDABCJEDGB@AJID@DFBLA@BGFCCGBEBAFLZBBBBCH@FDBHBCLDFCREBACCAODGAILKBBNBHKJmx",
                    ],
                    encodeOffsets: [[112750, 20508]],
                },
                properties: {
                    cp: [110.33119, 20.031971],
                    name: "海口市",
                    childNum: 1,
                },
            },
            {
                id: "460200",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@FDFFAF@DZRRD@B@LLTFDFFABJDLALPRDHADBHHLBJABCD@RdD@XMHDJHDBFFLDDLRE@ABCDDBABFRDREBDF@DDLDDADEJAFCFKDCTCVL@BEFBDJBBHFFAHBVCPCDEBAF@JCJBPBFDBDH@HBLBBF@BFJFANBHDFFDFBF@FCHA\\CRHJHF@FGLCD@VODINQLBFAHC@EACBMDIB@JHHDHEJBFFFJBLKVAFBHFJXZBLDFFDLDPDLLJ@NLJDNNNJNZNJHAFB@CHG@OCKFEACF@BC@CBGLU@GDCD@@A@CEIFGF@FDBBBFDABBB@LCFETIDCN@XFJEFALEJBFAL@DDFGBSDAFAZCPGFCBECWBG@A@EBC@OCCDMCEIGGIDIEEAQEC@I@ALI@GCGAIGGKFBMNMPE@ADABKLE@E@IBGFCJAJDFAFBDAFBBAH@@CTIHJNFNMHBDCFAJFF@D@DBBBDBDAFBDBDFDAF@LL@CJKJCHBJCB@DBHAD@@FBDLDFEDALFGN@DHF@HN@@LAF@JPTB@JIFAHI@@BB@HER@RDNBLFJLNFBFAB@@FCHDJCFBH@DP@NHHHDCNFNDDRBD@R@DH@HFHGD@HI@MBAECEQFOFENGV@BCJMHGFO@EAEGIAWCGCA]ECC@EDODEF[MEFGFBB@\\«UEQICCGUEmW{C]CgW¡QO]MeIgC_DUDO@QCeMc[YKWEWAUBMDWP_`IDO@}CUDMDGHM\\KJSH×VUJsRħI_BUBQLELIjMlEHGDSD½DAQCKGEGGCKGBGDGHYl",
                    ],
                    encodeOffsets: [[111547, 18776]],
                },
                properties: {
                    cp: [109.508268, 18.247872],
                    name: "三亚市",
                    childNum: 1,
                },
            },
            {
                id: "460400",
                type: "Feature",
                geometry: {
                    type: "MultiPolygon",
                    coordinates: [
                        [
                            "@@EGICEEDIEKDKEGAODIHEAIQMEKSUMGGKEW@EHGHAR@D@DEAQ@KCOBOBEHCBELABE@KGQE@GBGFIAACFMAEEBIAKAIGUHONO@GAQCSKK@KDGAQECEAE@CJGBC@CCCASLMIUBIDAJCFDL@HCHFLADEPB\\A@@CC@CFE@EFBDDF@@IFKDCAACCBABK@SCOIQEMGGCMAGDEDCHSBKDGAuCGGGAKEECEAOGIAGCKKNITEVCDEBMEUCaCCLSNQTAXAF@ZABKDIAAAAEAGE@GGEBCHCRADGHAHABKFEHEBAD@DGHEHAJGDADEPIDCNE@GGMAMIKCGCC@CFFB@DKBeKCACA[HBBFJDLBDTAAH@FHDBPHFFAFBAJHL@DC@CH@JFDH@DF@DCFEDG@@F@FGDELIJAFNLAFEDEHAFC@IIQCKBI@EGQWEMDOEEQKEEKEABMDCDGEC@G@IIGDEAE@KFEDDD@BEFADBF@DIDABEAAAA@CFEFC@@AAAAFE@DE@EEGCB@FA@CCCA@HABCEIBCRINIBIHA@EEA@ADBDAFCDAA@CGAEKCDAFABAC@CEEGD@HCDADCDA@CCBMAGC@A@W@@CFC@AAASB@ABGAAMFEFAHOAILM@AEC@A@AHA@IE@ECCO@ABEJQLGBOEECE@IFGJBH@JHNZRGP]AUBEFITINOFGFCHAJKTEHIACCAKCEEAEHEDGAWBIFCHUJODW@GBG@EEESB]NWBIEQMIWJWMGCM@KBGDEDBF@HAFCBEPAJDB@BABGDCDE`OBUHENGHKDIAEACBEHWvTVXRtX|lXhN\\Xj^b^NXHhDRDNLZ`DN@HMbELCLBd@PP^JJPHlTFHDXDFV\\JFPJL@PCFBPJBNFN@bFLDBF@LALEH@BBAJDHFD\\JN@rKFAVUFAJ@JBN@IQĘyPEDIFe@aAU@KJgDKHEXCJEHUAOAEBYAGGI@EGCKDBIKGIIEAKAKLC@@IAMDIDEDAJBNY@OEEXOJUIMAGHAF@VJJOHADEN@DCJJXBF@DCFID@@FFDBADEFBL@DBNAJB@ASEIMBEAIJACGDCBCAADGBD@JHK@AACF@@CF@@GBAAFDBEHAF@@JCDCBCBB@E@ABAAAB@BFB@DGB@FEBBGFADBBD@@EDABBNABEJKFAJJRJREBCJBIHC@DB@BFGHCDFCBH@BHBAAECCAEK@FGFABCDBHCL@DAJHPB",
                        ],
                        ["@@MEGBID@FDHRJNBP@dEjIHGBCACICGIC@KBCBI@]JCBAFM@GA"],
                    ],
                    encodeOffsets: [[[112404, 20049]], [[112059, 20391]]],
                },
                properties: {
                    cp: [109.576782, 19.517486],
                    name: "儋州市",
                    childNum: 2,
                },
            },
            {
                id: "469001",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@@AFSLKEEAK@IJKDKDANQHU@YJQDCbKDABMHMDAbAJYRFRADDBJJDF@TKFFPBREF@FFPHFFLALFNEFEPDHCFIfEBA@ECEMKGCKBGAUSAEBIHKHCHGHGBCBKAKAQ@OBCAAKCc@ECAECEFMJI@EIEEI@CFMKIAAHEDEAIBCHIBIJKDKPa@CCCAOAAAAIDEAK@MHKBEAGAIASBKEKB@IEIAGECAC@EDIEOCAGDCAIQ@EA@MJEFAHGDADE@CAIBIRGD@HCJKDK@AD@HDDJBD@H@DTAJKDCBICIDG@@AD@@EGEQGAKIEEOEGCAKCIG@EFGJaACCCAGDEHMDA@EGAOAAIEEI@SJiMI@IBMACFK@EFI@KDCBKMCMEKMMICa@CBCJGDEFGLHhAPKLE@IBAHCHEFEFONIFKRAF@LAPBHFH@DGRCPBDFB@DIP@LBFDBHADBED@B@JEZBJEH@NHJDLFFARBD@HFDBFNJDHADYbGDI@QFDFDB@DG@HF@DIJ@DBHILAHEHMBEJFBCHBFBDTLBJBFPDBFVEFCDGDCD@TJFD@LBDHBJHJ@TNHDAJNTNHHPDBNALBHBJDPBFDDHFbFZDDFCFEDALBVHRGJ@HFNCLD",
                    ],
                    encodeOffsets: [[112153, 19488]],
                },
                properties: {
                    cp: [109.516662, 18.776921],
                    name: "五指山市",
                    childNum: 1,
                },
            },
            {
                id: "469002",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@o·}WyocGcQÉ­FUBKFCHANC@CBIEE@GFSWIQKEE@GFQTOJQ@OKHaKOOKaAQGMGOG[S[KmMWCACC@@EBCAGBGAAACE@@CCAIAM@IEE@EAA@CHC@CCG@CKII[MMDQASIYEIHMTAFADADILECGEIBGAEBKEGBEFBLDHAFKBEAAAAQHMAGA@MAIDGRMHEJA@CCIQCJEFADDLFH@BGHQDINAHCBEBIHAHGBGZFF@JBFBPGf@^KlD@PPPTLT@P@NHNEZDPHLJ@Z[NGRFVJZHRHNDT@EZJ@XFLCZQL@JBJHJDZINB`\\RBJEFEFCJBHHDPCJGJCJ@LDVHLDDZDFJ@JALCLEFUHcTCNLTDP@DFXLJf@FFBLCP@PLTPHZBHBNLLXHFHAFCPCHFL^HJNNLJLBN@VIL@JAHDFFDRJNLJJBRCTEPDVDHcFITCJCPULW@QEQBGLGDKEiBKHK`KRH`VCXBJFPDDJANGFPJDLBPCVG¬Y",
                    ],
                    encodeOffsets: [[113388, 19844]],
                },
                properties: {
                    cp: [110.466785, 19.246011],
                    name: "琼海市",
                    childNum: 1,
                },
            },
            {
                id: "469005",
                type: "Feature",
                geometry: {
                    type: "MultiPolygon",
                    coordinates: [
                        [
                            "@@FHFBBBAHBDLBDB@DWBBDA@ECA@AJDBDAFDBDBBFHHDLPJBFAFJFCAEFKLETBF@HFNFDFELCZEH@DDHXNBDAHIDIJAFCDM@WEIBGRBFLJBFAHCVIHBFDNEJEDCHEFAFE@MLAAC@M@BFDLK`CBC@EH@NADC@EBAFK@IFWHGFEB@BDF@PCLMPIHMFEFENGHEB fjRPPLXLXJLDRRTTTRHDL@HA\\MLM`³N_JErETE\\SRWPUZSlQbGXCPVL\\H\\ANGJKFOhÉtý~ñrģFmEUMMWIQCASE¥{{gg{qiiQGOEuEEAIM«ZUHODKAICEOMHIBCCEOAIDW_UQGODOHGLALFjCLKHAHFR@RCLKTKNIDSDEJGdHHDTAJORGFeXMBK@mQM@GDCDCJC^BLJJLFNJHNJHLDVDLHNKB@BFFDXANDCI@GAEAEAACICCBEACPBD@FCFKDCFAD@FCH@FDH@DB\\DFBD@DEHBFADBHA@FDDLBFCPF@BF@DJHBDRAHBHCBEA@DFJCDENBL@\\BDJHDJHFFNHJBFCJDJCFDDD@AHLBHFHBFF@BC@UACBADCDSBGAGDEAONEHBF@NEVHHANCBGCI@IDBDHHHADBF@JHLAPDHADF@JCF]JCBAJGLAFHTHFDBDDDPHR",
                        ],
                        ["@@@HJD@CAAFK@CA@KJ"],
                        ["@@BDB@DBB@CGEB"],
                        ["@@BB@AA@"],
                        ["@@B@A@"],
                        ["@@FFFBAGEACB"],
                        ["@@@FB@@CAA"],
                        ["@@BBAA"],
                        ["@@@BBAA@"],
                        ["@@BDDAEA"],
                        ["@@BBB@CA"],
                        ["@@BHFAHK@ECACBGJ@B"],
                    ],
                    encodeOffsets: [
                        [[113296, 20243]],
                        [[113943, 20459]],
                        [[113936, 20444]],
                        [[113935, 20443]],
                        [[113930, 20442]],
                        [[113924, 20438]],
                        [[113872, 20402]],
                        [[113873, 20404]],
                        [[113875, 20391]],
                        [[113886, 20359]],
                        [[113885, 20360]],
                        [[113871, 20387]],
                    ],
                },
                properties: {
                    cp: [110.753975, 19.612986],
                    name: "文昌市",
                    childNum: 12,
                },
            },
            {
                id: "469006",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@cšO@cFqDa@_EeEQMWWU_O¥[AACY@sHA[AEGCOAŁcI@KBQTY@WsW]QdWBK@KBEDAJC@QBEGMEGIKCEFIJEBOZCBKAG@CBYVGNEB]@KCC@IFGHGNARMJI^@HEV@RDJBFEX@HDL@N`JBNAF@DLHHPJ@NID@FDHPJLBBH@BDEHDRDBNDDBRRJLBJENKNGRALQXUTKVW\\FJzXTJPFHDLLDLA\\FPtPPAPBFPPBFJRDDB@FINGHQJCJ@FBBHGN@PDDJ@H@BA@CCGAKDCFCD@LFFAHBJAHFFDJKBCBCBENSJGZFTJRBNC\\NJJDLH@DDD@DGB@FBF@JFN@JBDB@DF@BDBBAHBHAD@FD@BDXDnN\\L\\TPHNHRHbBPLLPGbPLR@PIRSHEF@LFJRTXHEF@JFDAD@BMDGLEVA®E",
                    ],
                    encodeOffsets: [[113266, 19543]],
                },
                properties: {
                    cp: [110.388793, 18.796216],
                    name: "万宁市",
                    childNum: 1,
                },
            },
            {
                id: "469007",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@BEE[SESBQEMOKGGIACAmAEKKSBSACCAECAKDM@KDMBKFGEQAECKOAEIKIDQBC@CEEAKBOHQCEBYBwOUIIGSKQQmQ_YccM@]DKAKKGFILOPKDOG{@ICUMGCTI\\ejqrapI^A^@TDTL^pp\\ZDFHTMäADaXIRUK¦ATôJFXNZbtZVYJOHUAEDKHCDE@CHKDETOBEBCDKDGJGNGTEXCNDJAfMxOD@LHFBX@LBJDPLRDFCHEHMJCNAJCp]\\BDAROPEJBJDNB`CLAHGHIDKLKBaHYFKNOFEJAL@NE@AIKOAEA@CDG@ERGF@NDHCFGBGFEDS@AEBCCEICACE@EDEDKAIICCEHIEa@EVULDREFDFH\\@FA\\QL@`GL@DCRuBA@IDC@EDYAIDICI@ECC@CGKAIMS@YMKCQBCBCNCPMDEDIDCNENK",
                    ],
                    encodeOffsets: [[111745, 19332]],
                },
                properties: {
                    cp: [108.653789, 19.10198],
                    name: "东方市",
                    childNum: 1,
                },
            },
            {
                id: "469021",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@HBDA@AEEBEACJADMFE@GDABEAEEIWKBG@EGIAEAWAMBC@GBCHCFGBMDC@EDA@AHBBCACD@AABCAEBA@ABGB@BEDBBCFAHBBAFFLADB@CBADDD@FCEICKBIFKJEJAHGF@H@RGFBDJ@DCBFHL@HCPCDB@BFLPFBAHCJGN@BAD]BAD@HCHE@CKGUCKCIGGMMIKEIIAKD]DIDCHCH@F@nRL@NAfWHEPQBICSGGUCOCSFQDIAKIIMCQEEGCIBK@UJM@KAKIMMGIK]GEODEDGBGEKWMKGAYAOGKS@ODOAKEEe@KIEW@CCOKSDMdSVGFEDKBUEIYCCCGKCU@KDIHIDICOGGIAEDEFIFQA_[MAYJICIGIAK@YRKDWEI@DXC`DTBlDJCDBHDF@BEPABEAE@CBAFMPCEM@SGIAEHCDHJABGBCBCJBDRRBFAJEHFHKFIEC@EFCHIH@FBNCHAHCHCPHJB~LRZTJNLHRAPGTCPDJR@jBLNJRALJ@LIRORIDKBOJO@IF]NAD@NBBFBDB@DEB@DDNAFCLBN@BEBEFCHBLCDG@GCEFABECCBKKABMCAADCAGBCGA@CDAICBAGCBEI@CAACCA@EA@IFAJCDADBRTD@HI@@JAD@FC@CCCCACE@CFCFBJFFDDRHHJ@HAPKXGXFHTBHL@JHJRFNEB@FARO@CCEDIAEFGF@DA@IHAXKJOLDDAJEDKD@HDBDCHGDCJFFDHFBHJN@A`DFNHNBHHALJVAHBJH@FDF@FCFHRBJ@DBJADANEBAJDFFHPDDFJPDFBDDFBFAJEDAJFDAfCDFBT",
                    ],
                    encodeOffsets: [[113028, 20202]],
                },
                properties: {
                    cp: [110.349235, 19.684966],
                    name: "定安县",
                    childNum: 1,
                },
            },
            {
                id: "469022",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@HCBFDBBDDBJ@AFHDABJDCB@DHBADBHCDBBNDBALLDAFDBAFEHDH@DCAKDGFEFA@AAMDKBECM@CFA@CCAEAAA@MBC^MJEP@PILAJCPQJQ@KKIQBMIAK@iIQOCSDOHQBKGIMYSKQA}GIDODGBGDGAM@EJGDGFED@JFLEEGFGBIAEQQACDIDAHABAGIDCFGJBTHN@DFNOBEDAF@FBBAFO@ACEAGDCCIAkCSD_CWFYS@MCQGYGUIQEMHY\\I@GKCOFYGM@M@OKSOSOOC@KJODO@S@eIQAKHEHAPGPSPCDCJDHEBAAAAQDEAGFCAI@CHEB@DBDEBAFCAADa@GA_CGN@FBT@HGNKNMLOFMJKBKA_AQRcnEFGDMBM@CCA@MLQBQVDdDFCJDHD^@DGDFHHDHFF@LJ@VFPLTPJJBJC@DDBDCFBHIHGJ@D@PNRBJJ@FGA@DC@@BDDJBBD@DELIAC@ADFBJBFB@F@NDJDBFED@RDNAFB@DGLICEBGB@FBFDDF@JH@LJLCH@BLBDB@DIBKN@BDHALVBZFXA`KRANBbFJCJEDIDYHKNCTFTHNJDJ@JGNDPRJLBdAPDPJAJCHILBLDD@FADEFCAABCACBBDDDCHEFBBAHNDD@FABABB@BFBBBBBADFBJHFAJ@BABB",
                    ],
                    encodeOffsets: [[112781, 20030]],
                },
                properties: {
                    cp: [110.102773, 19.362916],
                    name: "屯昌县",
                    childNum: 1,
                },
            },
            {
                id: "469023",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@nwLIAGAMLAJKHBPCDBBDDAB@BGBICEDKGACA@EDGAAAAKYBEFAHADDHE@AKBEA@CJCBIA@CHIFADCBBEAAEAACG@ADCBA@CG@IFINKJ@FG@CMEECEIBELCHGAU@CDE@EQBGCE@@ABIDCH@NHLJFB^KBBNDDDBA@AFSGAOBGG@ENAJBHAXQBQDE@E@GGQBAJgHI@IZKDCCUFKDABACAEBEMME@KEEAIEC@ABSJAR@BIDCBAAAEMASGEBGLIF@VJrH@EIQBKGGMAICEE@cM@GIEACGEEDIHCDGACGCC@CLIFCBKCIPWLGB@JCBE@EHBFCJDF@DQPEBA@MFQEGI@IGKSAEGHWLWBO@GGIQGCCEEAIDEDEF@BDDDDDD@@EBC@IJ@@GSCAQBCDCBIBAAAABI@EBIGEABCAAAAEA@AAAABEBC@MCBGAAFEDGCCACDADBBADBFEBC@ECCAKJKDGBIOIOCcBKAQICOHM@ICIMISGSEMDGLCZCJIFIDaEMAQB_LWBYEUABKCG@ALMJA@CCAKA@ADGIK@KIGE@CCAE@EHAFAJDHK@CEAMBQCC@EFCACI@M@EEAIAEABCD@JBFK@CACIACC@AD@@CHB@EIIQAQMI@C@EHOVIBBL@JIJGBCBABHJADEBEEBGCGGEOCAI@CJCLGDABAACIBGIA@GJC@ONC@ICIGQAKKMAECAMI@AHGBE@EHEFABDJKPUFY@OLBFENBDJBHEHAF@HR@LAFKBAFGDAFAPDP@LBRCFC@Q@GBGH@FFXHLNHTVFLRNBJGFCJBPFHCLFLCJFFJDDFHDFHBHJNHT@FDBH@FGLGLAJBRELBPJCH[HENBJHFLJDDBPFHNHTDLFDJ@JDNJR@VBPFL\\`HLBXFNCNANJBBBFL@JDJDL@DEHGDEJWJADFT@JFFJD@DCLUF@FDJLBFBB\\KDI@CJCBMAGBORQDHJFBDFAHKPLBJALPFQDAHBDC@CHABCFBLNHV@^BLYFIRc¤ZFPBpCbK`OZBTÄ",
                    ],
                    encodeOffsets: [[112750, 20508]],
                },
                properties: {
                    cp: [110.007147, 19.737095],
                    name: "澄迈县",
                    childNum: 1,
                },
            },
            {
                id: "469024",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@X|VLR~p^\\NJNDP^@^NTRJDNDP@TCN@dHL@NCTK^cZUNCXAPBLDZRNFNDR@LALG\\Kd£JQZEAK@]GUKMEAADGB@DCDGACBERKOIBKALOBGCEEAGIRCPQHANBDADIJ@LCA[EAKACI@EVEDK@CICEE@IESBCXIFIHCFG@CCKCI@IEKAAIABMDMEMAWGK[_EKAO@UIQCM@ICIKESCMGEGAOCCKIGEAIFM\\GDGOIKAQFIAKBKHEHG@CA@EGSIMAGEGEAOAIGCBK@GDCAADEBEHL@BFDDBFABAGG@DACEGDEH@ACAD@JGIAADQFQIIIEBILAFMBAACB@FC@AABCHEAAEFA@CHA@AEA@BBAB@B@FAAADCDIDBEFGCABEAB@HE@@DE@BD@BGL@IACCHBBADCDDHIBBJAFJNTF@BIAMBCAK@EACFABEC@EC@EJCDE@WAIICDM@CFGBIPUIE@GBBHJNIVWPFF@PMZIACBCFCJBN@JD@LKLBFBJJLHAJLCHD@FHJBHAZBFBPGVIFWDGFCLIhDxGrCJOF·`",
                    ],
                    encodeOffsets: [[112127, 20351]],
                },
                properties: {
                    cp: [109.687697, 19.908293],
                    name: "临高县",
                    childNum: 1,
                },
            },
            {
                id: "469025",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@PCVIDGJEXAHBFCFGFBDFBLDDJBFGLSBIDGHEPEJMJSFEVA^BHOYQGM@IAGHIJEF@FDPFHARKFIBAP@DD@FJFB@BGB@D@BFN@JKPBBGFENEBBAH@BTABB@BED@DX@B@D@BHANDDB@DCBCDC@GHCFF@DBDBABEDCFLHB@DBBDCBEACBCB@FFB@JGJAJMDQJADFBA@GDBDDB@@EDAFH@FCFF@BEBB@BD@FEDEB@BBFBBAJC@CAEBCFE@ACCFCLEF@FBHCJJH@D@HFDCNCBALFFFRLFFCPFNRXFHJ@LARDJJD@BEFGFCBEMKBEJIFKHC@E@EH@FCDE@CCEG@EC@IDGD@@CGKBIEAEBGEAOGC@EBGSBACCKEIAA\\GDBDBfLLA@CEADED@HDLDNJNBHHF@DMJCFOBCHCBIFGHG@CBCFAFGLEBABGHGBCDQDGFAHHF@BHBFBBJBNC@[BEBWRSTMDKrFTHFADAFWJSLMCKJSBCTKBICQDKACY_YTW@IGGMAKBMAAICKIOCIBE@EGUKEG@EJ]CMGEEAKAw`OFOBIAGCCCEECE@QCMAMKCIGIEKCMDGEI@QHUGKAEBGHC@G[EaCGECOAICGAKAMBCAGOMGMSBIGCSMI@IGGAAC@G@CECSIEBEJED]HMJKCC@IFeLKFCCIDS@AHBTILADBBDFJNBD@FAHEDCFD`AFCDBJCFAHCFDLBNCH@JKDKECBM@KFINMAI@CDGDGCG@IRKHMDIAOIGAGAIBMtKXEHANFVCLIJk\\KNM^ETBLXnRrBNBRIPGHGJKLGTADIAGCK@SLKTCTIL]@QFKFSRERBRDHHHJL@VIVCNCjBNNJFRAJMXA^FTFFH@HAX@",
                    ],
                    encodeOffsets: [[111689, 19955]],
                },
                properties: {
                    cp: [109.452606, 19.224584],
                    name: "白沙黎族自治县",
                    childNum: 1,
                },
            },
            {
                id: "469026",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@ASDcDMJU@UIKGGCGAQFQTQLERE^@JKDSLSTKL@HDJBBCHSLKHIHGJOAQAMQqWmAKFSN]LMl[JIDKEUBMFGLWNsJAHBHBPJJBNCLGJQH@HDHCDCJ@NBJMLEN@DALFLC@IDGAMCKDEBGDEAIDCBEC_DEFCBG@EACMSACLMASBGT@JC@EGOG@SUMCIGGYB[AAEAKAACEAMCOBQAGGECKDOAYNEDCHKDKDS@GGSBKGQ@EQQ[EEA@MLMFCDCJCFONMDADADDRNL@ZNTBJHL@DDD@FDJCJBJCZ@FCD@JABQvCDK@_HK@[REB[@EGECQFKCUV@FFbGJDFJDBJCLCF@FDFDBFJDDFA@BCTEFAHEHGDMCE@QH@FCH@DFBPBJL@BMFK@IBEFMPELGZAbKLCLGJGHKB_DMAICIAOFQPCB[Ao^IDMBIDGNGFEDQCOKICKAW@EAKGC@wPeNIBMCWDSFMHIHCHCLADAFSPCFGL@DCFGDCLBFGVIPUZNVZ^`N\\LXDBTDdRNNj\\XbNhLZLjXuFGDAFBJBLCHGFMVGPAF_DCHCBA@ACABIFODABE@GAEFCHCLAN@HDXNXI",
                    ],
                    encodeOffsets: [[111662, 19897]],
                },
                properties: {
                    cp: [109.053351, 19.260968],
                    name: "昌江黎族自治县",
                    childNum: 1,
                },
            },
            {
                id: "469027",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@EAGBIEEECMGIMIMMICMKI@MKMCQGCEAKWYEIAGBELUAKEIEEIAGFGCIGA@CJANBD@FGDEBKAMRCJUPC@KDEHE@IGQG[DGBEDE@EAECCEAGBMIEAEE@AAAK@GCGCAAEAODI@IBEFADCDOAUBGEEAGIAACFE@AUKSDCDELEDIBCFCBKCCCE@ACQFQCAEABCCAD@BQFCKKCEECAIGGCWNC@QcC@ADIBKAGGCAGBQCKOKBICBAEEECKS@K@AQCYQ@CBEEEECw®apIFCBsBTqTkJÇDkHePWNQXIZGtChDbÆNIHVNJD|@PHLCPOJKHELLLB^CN@dd`ZnRRRTLJHVJxPZAFARDPGLAFBDFD@RAJCJLBFLPFDRBHFLENALCN@LCDBBFDDTBVAJLBFBnBDHJLHNPRFTATFF\\AFHFR\\FRP@NHTAHHT@XGDGFCVKFANBJCHDHHRBPANDFBDFPBBFAXHZJHNDTVH@B@FP@FDDLEfKJED@LDNIHAAEOCAEAISKCIDGEAFINAFGBGJKAGJOACECF@BAGIREJ@HCZaBCCGMIAEEC@GACBQEECKGI@MFGAIFY@I@AFCCAGBCAAE@KJO@CEAACDOHQ@CEGAGBO@KBELQJEPMFEFEDGBGJAF@LKBOGgHKFEHCDKEG",
                    ],
                    encodeOffsets: [[112031, 19071]],
                },
                properties: {
                    cp: [109.175444, 18.74758],
                    name: "乐东黎族自治县",
                    childNum: 1,
                },
            },
            {
                id: "469028",
                type: "Feature",
                geometry: {
                    type: "MultiPolygon",
                    coordinates: [
                        [
                            "@@@MCK@GFWAECI@IF]@GJ]NIBQHMHGLEND^@FAHMZUDAH@LBDAPYFAJIFELDHJNFFHRAD@BIFCLAL@XAcµaQe_IKQaM}U»GOKQSK¡aOA_BSFuReFsBË][[¬A@EAEHNFE\\CFCP@FDD^FDBDHBXHJBF@FEPGHINADC@Q@MHEFEPFRFDJAH@JJJAHHD@BE@EBGHAFB@FDFDELCJDNTDJALCFBNPHD@FHDB@LDF@DCHEB@F@DQCCAC@CDI@EDANAFEDG@CAGD@@@FEBEJDJ@NAH@FFXALLDHHNBJCDB@NALCHEJAHDDN@B@BJDDFRORIRGDANBD[@CBCBCN@PBDC@QIYEA@MJAD@JLNADOH@BHdAB_HABDPCLBRNLDLRRDIACBADA@CBAFGP@`[BGBGHIAOBQFOJ@B@HKPQJ@NFJ@RCDBNPJFDLBBLAJPFDFABAHQFIDAF@BHJFJHHHHLJBFFL@HJJF`DN@ROJBFEDKLGDEBKPKHIHCL@",
                        ],
                        ["@@DBBAECADB@"],
                    ],
                    encodeOffsets: [[[112656, 19183]], [[112788, 18878]]],
                },
                properties: {
                    cp: [110.037218, 18.505006],
                    name: "陵水黎族自治县",
                    childNum: 2,
                },
            },
            {
                id: "469029",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@QQCKKGACAIDSCOBA`GBAGc@APGBCKM@IDENGZFRJD@AC@ODMDADA\\@ACBMHCJQPQEQCCAIA@M@CCBGFIDGBK@MCAIDMAGGIC@KE]BOCOFIFA@EHCDBH@FCBEBMFCJ@DCD@DBRD@C@EFADG@CCE@KCAEGC@OGAMDEBKCIMSICKDCFCE@EEAGBAH@FAFA@EACEIBIIG@IBABANEJC@GHGEG@@C@QACCQMCMECDGGMGO@@CAGDECIDG@EA@EBEAKMEIAKCM@QFQ@GAA@@GJEBIJA@OS@IBE@KM@@GGE@CHMKECBEFKCAC@EC@GBCAA@IDGAIDIL@DKKE@CBCECAEACBCAAACAC@E@IEEBCDGAMNMEGISJ@DG@ABEACBEAEBICOFAH@J@FKFALCB@BOFMNANLEHHBJDH@HKJ@B@JFDBRFFCJHJJHDFCNDD@PAD@F@BAHDXAFEDOHYDEBCBATEHCCK@EBIAKFEBIFWEM@CDSJEFKDA@AACBAEAAECE@EHFJ@D@BC@CD@HKVAH@DADE@BDEFDL@PGH@DFHF@V@N@FDNNFLDNLNDALCJ@FEL@DENBJAJ@jNTIJ@FFBJPBHB@FCBGNCFBHDDBDIbEH@FJHLDDBFHFPJFBLRHHF@FC@@BH@JCJDDALCBICSG@C@IACC@GBCL@LCDI@GHCJQJADBF@BCHCBGFENIB@@FJRDBHCDBFPCJ@FBDFDBHFJ@JLALFTAJBHBFBLANGL@FBLABBBPDD@DObCLILAJGJADBJCFGFBBLJENBJNJ@HIHENDFBFFDd@LDBBLAJGHAPQFAJANDL@LDD@JGFO",
                    ],
                    encodeOffsets: [[112409, 19261]],
                },
                properties: {
                    cp: [109.70245, 18.636371],
                    name: "保亭黎族苗族自治县",
                    childNum: 1,
                },
            },
            {
                id: "469030",
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: [
                        "@@EAEDAA@CIDIAOIKSEO@UKIE@GEGCEGHC@CC]CGDICEA[AEBEPQRANKB@DDN@NAHCFEdmRQ`BLBLANIPENKLMHM@GAS@EHM`DHBb@BCDBBEFAAC@CFADGJ@DBHEFBRCBBBBFACGDIDCTOHOBOFGLGRBfJd@PCLILk@]HeAOAE@IEEHYHABGJGFADABGJMRCHG@AEGCKBCFEDMAAOOAEBOOOsEOB[CKKKGCOESIyWEIX[LUVSRWBKHQLMFMAIIKQQCAMCCACQFGACG@AAIKGOECC@MJI@GOKG@CBEAM_IK@GDGJOLALCFKHCLEFIAQPM@_CIEGIK@EEIAGKGGIGIEAGE@CBEJGRABEBECIOKBAACKIEIKEEYDIAGCKBMPGLA@I@EPARBPGJAHAH_\\O@EHAB@DCBABBDADIVIHMCK@MCIBEBORGBGHMBAD@PBRBLALADGHGHGDGLAJBFVTHBLAHDRR@DADeFEJGDCAIAGFMFKEKBEEOGEEE@QFOAEESLE@ICAICCQBQEIZaBCBGNANCBaLCDIR@ZGVMRCBCLIL@JBLFFKLET@BJFFFRF@NDN@RJLLHPBZGx_LBFBHFDNI^@FFHVLFHF@JAPDLJJDBBANBLHNJHX@ZS\\bCNDRAJSLADGPADHXBHHJBPDFFFBLHHDHBvCHALGTCDCFBHDNHHFNJRDP@TALABDDBBCDEL@JE@CCEA@FEF@DDD@@[BOACFKBGEGDK@ECIDCBAJJVKNBTDD@DADIH@DBHDDVHD@LCL@TLRDHBP@PMVGNHRDVMZ@VELOCIBAFEFGLABABEHABB@DBJFDNBLLRBJHJDD@PMD@HIB@HJJABDABCBKHID@HBFPDHFDHAHDDDBDABCGIBADAHAFEDGAQJAHK",
                    ],
                    encodeOffsets: [[112514, 19853]],
                },
                properties: {
                    cp: [109.839996, 19.03557],
                    name: "琼中黎族苗族自治县",
                    childNum: 1,
                },
            },
        ],
        UTF8Encoding: true,
    });
});
