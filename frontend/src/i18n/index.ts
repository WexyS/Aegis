import { en } from './en';
import { tr } from './tr';

export type Language = 'en' | 'tr';

type DictionaryShape<T> = {
  readonly [K in keyof T]: T[K] extends string ? string : DictionaryShape<T[K]>;
};

export type Dictionary = DictionaryShape<typeof en>;

export const dictionaries: Record<Language, Dictionary> = {
  en,
  tr,
};

export function dictionaryFor(language: Language): Dictionary {
  return dictionaries[language] ?? dictionaries.en;
}
