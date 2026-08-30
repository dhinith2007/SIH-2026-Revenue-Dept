export interface RevenueServiceItem {
  id: string;
  code: string;
  name: string;
  marathiName: string;
  category: 'CERTIFICATE' | 'LAND_REVENUE' | 'TAX_EXEMPTION' | 'SOCIAL_WELFARE' | 'OTHER';
  description: string;
  deliveryDays: number;
  issuingAuthority: string;
  requiredDocuments: string[];
  isPopular?: boolean;
}
