.headers on
.separator ","
SELECT ROI_1.id,ROI_1.t,
   ROI_65.xy_dist_log10x1000,
   ROI_66.xy_dist_log10x1000,
   ROI_67.xy_dist_log10x1000,
   ROI_68.xy_dist_log10x1000,
   ROI_69.xy_dist_log10x1000,
   ROI_70.xy_dist_log10x1000,
   ROI_71.xy_dist_log10x1000,
   ROI_72.xy_dist_log10x1000,
   ROI_73.xy_dist_log10x1000,
   ROI_74.xy_dist_log10x1000,
   ROI_75.xy_dist_log10x1000,
   ROI_76.xy_dist_log10x1000,
   ROI_77.xy_dist_log10x1000,
   ROI_78.xy_dist_log10x1000,
   ROI_79.xy_dist_log10x1000,
   ROI_80.xy_dist_log10x1000,
   ROI_81.xy_dist_log10x1000,
   ROI_82.xy_dist_log10x1000,
   ROI_83.xy_dist_log10x1000,
   ROI_84.xy_dist_log10x1000,
   ROI_85.xy_dist_log10x1000,
   ROI_86.xy_dist_log10x1000,
   ROI_87.xy_dist_log10x1000,
   ROI_88.xy_dist_log10x1000,
   ROI_89.xy_dist_log10x1000,
   ROI_90.xy_dist_log10x1000,
   ROI_91.xy_dist_log10x1000,
   ROI_92.xy_dist_log10x1000,
   ROI_93.xy_dist_log10x1000,
   ROI_94.xy_dist_log10x1000,
   ROI_95.xy_dist_log10x1000,
   ROI_96.xy_dist_log10x1000
 FROM ROI_1
 LEFT JOIN ROI_65 ON ROI_1.id = ROI_65.id
 LEFT JOIN ROI_66 ON ROI_1.id = ROI_66.id
 LEFT JOIN ROI_67 ON ROI_1.id = ROI_67.id
 LEFT JOIN ROI_68 ON ROI_1.id = ROI_68.id
 LEFT JOIN ROI_69 ON ROI_1.id = ROI_69.id
 LEFT JOIN ROI_70 ON ROI_1.id = ROI_70.id
 LEFT JOIN ROI_71 ON ROI_1.id = ROI_71.id
 LEFT JOIN ROI_72 ON ROI_1.id = ROI_72.id
 LEFT JOIN ROI_73 ON ROI_1.id = ROI_73.id
 LEFT JOIN ROI_74 ON ROI_1.id = ROI_74.id
 LEFT JOIN ROI_75 ON ROI_1.id = ROI_75.id
 LEFT JOIN ROI_76 ON ROI_1.id = ROI_76.id
 LEFT JOIN ROI_77 ON ROI_1.id = ROI_77.id
 LEFT JOIN ROI_78 ON ROI_1.id = ROI_78.id
 LEFT JOIN ROI_79 ON ROI_1.id = ROI_79.id
 LEFT JOIN ROI_80 ON ROI_1.id = ROI_80.id
 LEFT JOIN ROI_81 ON ROI_1.id = ROI_81.id
 LEFT JOIN ROI_82 ON ROI_1.id = ROI_82.id
 LEFT JOIN ROI_83 ON ROI_1.id = ROI_83.id
 LEFT JOIN ROI_84 ON ROI_1.id = ROI_84.id
 LEFT JOIN ROI_85 ON ROI_1.id = ROI_85.id
 LEFT JOIN ROI_86 ON ROI_1.id = ROI_86.id
 LEFT JOIN ROI_87 ON ROI_1.id = ROI_87.id
 LEFT JOIN ROI_88 ON ROI_1.id = ROI_88.id
 LEFT JOIN ROI_89 ON ROI_1.id = ROI_89.id
 LEFT JOIN ROI_90 ON ROI_1.id = ROI_90.id
 LEFT JOIN ROI_91 ON ROI_1.id = ROI_91.id
 LEFT JOIN ROI_92 ON ROI_1.id = ROI_92.id
 LEFT JOIN ROI_93 ON ROI_1.id = ROI_93.id
 LEFT JOIN ROI_94 ON ROI_1.id = ROI_94.id
 LEFT JOIN ROI_95 ON ROI_1.id = ROI_95.id
 LEFT JOIN ROI_96 ON ROI_1.id = ROI_96.id
;
